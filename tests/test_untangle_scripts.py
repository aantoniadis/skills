"""The untangle scripts: change coupling from history, import edges, the stated design against the edges,
the leads to special cases, the units, values, and edges a change adds, the tests that execute a line, and the
source behind a note's pinned lines. The first six print leads; the tests pin what they find and what they leave out."""
import importlib.util
import json
import os
import re
import shutil
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/untangle/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coupling, imports, conformance, cases, tests_for_line, pinned, shared, breaker, values = (load(name) for name in (
    "change_coupling", "import_edges", "design_conformance", "special_cases", "tests_for_line", "pinned_lines", "shared_data",
    "break_probe", "added_values"))


class Repository(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")

    def git(self, *args):
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        return subprocess.check_output(["git", "-C", str(self.repo), *args], env=env, text=True).strip()

    def write(self, files):
        for name, text in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    def commit(self, files):
        self.write(files)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "fixture")

    def run_script(self, name, *args):
        result = subprocess.run([sys.executable, str(SCRIPTS / f"{name}.py"), *args], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout


class ChangeCouplingTests(Repository):
    def test_pairs_count_shared_commits_and_skip_bulk_commits(self):
        changes = [["a.py", "b.py"], ["a.py", "b.py"], ["a.py", "b.py", "c.py"], ["a.py"],
                   [f"bulk{i}.py" for i in range(5)] + ["a.py", "b.py"]]
        revisions, shared, bulk = coupling.analyze(changes, keep=lambda path: True, max_files=4)
        self.assertEqual((revisions["a.py"], revisions["b.py"], bulk), (5, 4, 1))
        self.assertEqual(coupling.pairs(revisions, shared, min_shared=3), [(3, 67, "a.py", "b.py")])

    def test_a_partner_outside_the_scope_counts_and_a_commit_outside_it_does_not(self):
        changes = [["svc/a.py", "docs/a.md"], ["svc/a.py", "docs/a.md"], ["docs/a.md", "docs/b.md"], ["other/x.py", "other/y.py"]]
        revisions, shared, _ = coupling.analyze(changes, keep=lambda path: True, scoped=lambda path: path.startswith("svc/"))
        self.assertEqual(dict(shared), {("docs/a.md", "svc/a.py"): 2})
        self.assertEqual((revisions["svc/a.py"], revisions["docs/a.md"], revisions["other/x.py"]), (2, 2, 0))
        self.assertEqual([coupling.kind("svc/a.py", "docs/a.md"), coupling.kind("svc/a.py", "tests/test_a.py"), coupling.kind("a.py", "b.py")],
                         ["document", "test", "code"])

    def test_report_marks_pairs_without_a_dependency_and_leaves_out_deleted_and_generated_files(self):
        for round_ in range(3):
            self.commit({"shop/pricing/discounts.py": f"RATE = {round_}\n", "shop/quotes/builder.py": f"RATE = {round_}\n",
                         "shop/api/views.py": f"from shop.pricing import discounts  # {round_}\n",
                         "gone.py": f"{round_}\n", "package-lock.json": f"{round_}\n"})
        self.git("rm", "-q", "gone.py")
        self.git("commit", "-q", "-m", "remove")
        (self.repo / "edges.tsv").write_text("# from\tto\nshop/api/views.py\tshop/pricing/discounts.py\n")
        out = self.run_script("change_coupling", "--edges", "edges.tsv", "--since", "10 years ago")
        self.assertIn("History: 3 commits since 10 years ago changed the scope", out)
        self.assertIn("3\t100%\tcode\tdifferent\tinside\tnone found\tshop/pricing/discounts.py  <->  shop/quotes/builder.py", out)
        self.assertIn("3\t100%\tcode\tdifferent\tinside\tyes\tshop/api/views.py  <->  shop/pricing/discounts.py", out)
        scoped = self.run_script("change_coupling", "--since", "10 years ago", "shop/quotes")
        self.assertIn("3\t100%\tcode\tdifferent\tone outside\tnot given\tshop/pricing/discounts.py  <->  shop/quotes/builder.py", scoped)
        self.assertNotIn("shop/api/views.py  <->  shop/pricing/discounts.py", scoped)
        self.assertNotIn("gone.py", out)
        self.assertNotIn("package-lock.json", out)
        self.assertNotIn("WARNING", out)

    def test_shallow_clone_is_called_out(self):
        self.commit({"a.py": "1\n"})
        self.commit({"a.py": "2\n"})
        clone = self.repo.parent / (self.repo.name + "-shallow")
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{self.repo}", str(clone)], check=True)
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(clone)]))
        result = subprocess.run([sys.executable, str(SCRIPTS / "change_coupling.py"), "--repo", str(clone), "--since", "10 years ago"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING: this clone is shallow", result.stdout)

    def test_invalid_repository_exits_2(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "change_coupling.py"), "--repo", str(self.repo / "missing")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


class ImportEdgesTests(Repository):
    def test_python_javascript_and_java_imports_resolve_to_tracked_files(self):
        self.commit({
            "svc/src/shop/__init__.py": "",
            "svc/src/shop/pricing/__init__.py": "",
            "svc/src/shop/pricing/discounts.py": "import os\nfrom typing import Any\n",
            "svc/src/shop/pricing/rounding.py": "from . import discounts\nfrom .discounts import rate\n",
            "svc/src/shop/api/views.py": "from shop.pricing import discounts, rounding\nimport shop.pricing.discounts as d\nimport config\n",
            "other/config.py": "",  # a one-word name elsewhere is more likely an installed package
            "web/src/app.ts": "import { total } from './lib/total';\nimport x from 'react';\nconst y = require('./util.js');\n",
            "web/src/lib/total.ts": "export const total = 1;\n",
            "web/src/util.ts": "export default 1;\n",
            "engine/src/main/java/com/acme/Order.java": "package com.acme;\nimport com.acme.price.Rule;\nimport java.util.List;\n",
            "engine/src/main/java/com/acme/price/Rule.java": "package com.acme.price;\n",
            "svc/tests/test_views.py": "from shop.api import views\n",
        })
        with_tests = self.run_script("import_edges", "--tests")
        self.assertIn("svc/tests/test_views.py\tsvc/src/shop/api/views.py", with_tests)
        out = self.run_script("import_edges")
        edges = {tuple(line.split("\t")) for line in out.splitlines() if line and not line.startswith("#")}
        self.assertEqual(edges, {
            ("svc/src/shop/pricing/rounding.py", "svc/src/shop/pricing/discounts.py"),
            ("svc/src/shop/api/views.py", "svc/src/shop/pricing/discounts.py"),
            ("svc/src/shop/api/views.py", "svc/src/shop/pricing/rounding.py"),
            ("web/src/app.ts", "web/src/lib/total.ts"),
            ("web/src/app.ts", "web/src/util.ts"),
            ("engine/src/main/java/com/acme/Order.java", "engine/src/main/java/com/acme/price/Rule.java"),
        })


    RUBY = {
        "lib/locker.rb": "class Locker\n  def full? = false\nend\n",
        "lib/depot/delivery/base.rb": "module Depot\n  module Delivery\n    module Base\n      def zone(order)\n        order[:zone]\n      end\n    end\n  end\nend\n",
        "lib/depot/delivery/locker.rb": "module Depot\n  module Delivery\n    module Locker\n      extend Base\n      KIND = \"locker\"\n    end\n  end\nend\n",
        "lib/depot/rates.rb": "require_relative \"delivery/base\"\nmodule Depot\n  module Rates\n    # Delivery::Nothing in a comment\n"
                              "    def self.for(order) = Delivery::Locker::KIND == \"Locker\" ? 1 : ::Locker.new\n  end\nend\n",
    }

    def edge_rows(self, *args):
        out = self.run_script("import_edges", *args)
        return [tuple(line.split("\t")) for line in out.splitlines() if line and not line.startswith("#")]

    def test_ruby_constants_resolve_as_ruby_looks_them_up(self):
        self.commit(self.RUBY)
        self.assertEqual(set(self.edge_rows()), {
            ("lib/depot/delivery/locker.rb", "lib/depot/delivery/base.rb"),   # extend Base, found in the enclosing Delivery
            ("lib/depot/rates.rb", "lib/depot/delivery/base.rb"),             # require_relative
            ("lib/depot/rates.rb", "lib/depot/delivery/locker.rb"),           # Delivery::Locker::KIND resolves to the unit
            ("lib/depot/rates.rb", "lib/locker.rb"),                          # ::Locker is the top-level class
        }, "a namespace several files reopen, a comment, and a word in a string give no edge")

    def test_added_edges_carry_the_cycle_and_the_first_dependency_between_directories(self):
        self.commit(self.RUBY)
        base = self.git("rev-parse", "HEAD")
        self.commit({"lib/depot/delivery/base.rb": self.RUBY["lib/depot/delivery/base.rb"].replace(
            "        order[:zone]\n", "        order[:zone] || Rates.for(order)\n")})
        head = self.git("rev-parse", "HEAD")
        rows = self.edge_rows("--base", base, "--head", head)
        self.assertEqual(len(rows), 1)
        source, target, notes = rows[0]
        self.assertEqual((source, target), ("lib/depot/delivery/base.rb", "lib/depot/rates.rb"))
        self.assertIn("closes a cycle: lib/depot/rates.rb -> lib/depot/delivery/base.rb -> lib/depot/rates.rb", notes)
        self.assertIn("first dependency of lib/depot/delivery/ on lib/depot/; lib/depot/ depends on lib/depot/delivery/ too", notes)
        self.assertEqual(len(self.edge_rows("--rev", base)), 4, "the edges at an earlier commit")
        self.write({"lib/depot/labels.rb": "module Depot\n  module Labels\n    def self.text(order) = Delivery::Base.zone(order)\n  end\nend\n"})
        self.assertEqual([row[:2] for row in self.edge_rows("--base", head)], [("lib/depot/labels.rb", "lib/depot/delivery/base.rb")],
                         "the working tree counts an untracked file")


    def test_cycles_lists_files_and_directories_that_depend_on_each_other(self):
        self.commit({"app/a.py": "from app import b\n", "app/b.py": "from app import a\nfrom lib import c\n",
                     "lib/c.py": "from app import a\n", "lib/d.py": "x = 1\n"})
        out = self.run_script("import_edges", "--cycles")
        self.assertIn("Cycles: 1 groups of files that depend on each other; 1 pairs of directories that do.", out)
        self.assertIn("3 files: app/a.py, app/b.py, lib/c.py", out)
        self.assertIn("app/ <-> lib/", out)
        self.assertNotIn("lib/d.py", out)

    def test_coupling_counts_fans_and_flags_dependencies_on_less_stable_directories(self):
        self.commit({"api/views.py": "from core import rules\nfrom core import money\n", "jobs/nightly.py": "from core import rules\n",
                     "core/rules.py": "from core import money\nfrom db import store\n", "core/money.py": "x = 1\n",
                     "db/store.py": "from tools import fmt\nfrom lib import io\n", "tools/fmt.py": "y = 2\n", "lib/io.py": "z = 3\n"})
        out = self.run_script("import_edges", "--coupling")
        self.assertIn("Files with the most dependencies (fan-out):\n2\tapi/views.py\n2\tcore/rules.py\n2\tdb/store.py", out)
        self.assertIn("Files the most files depend on (fan-in):\n2\tcore/money.py\n2\tcore/rules.py", out)
        self.assertIn("core/\tCe 1\tCa 2\tI 0.33", out)
        self.assertIn("db/\tCe 2\tCa 1\tI 0.67", out)
        self.assertIn("Dependencies on a less stable directory: 1\ncore/ (0.33) -> db/ (0.67)", out, "a stable directory leans on a volatile one")


class DesignConformanceTests(unittest.TestCase):
    def test_every_relationship_gets_one_result_and_unmapped_files_are_listed(self):
        components = {name: [conformance.pattern_regex(p) for p in patterns] for name, patterns in
                      {"api": ["shop/api/**"], "pricing": ["shop/pricing/**"], "quotes": ["shop/quotes/*.py"], "storage": ["shop/db.py"]}.items()}
        allowed = {("api", "pricing"), ("quotes", "pricing"), ("pricing", "storage")}
        edges = [("shop/api/views.py", "shop/pricing/discounts.py"), ("shop/api/serializers.py", "shop/db.py"),
                 ("shop/pricing/discounts.py", "shop/db.py"), ("shop/pricing/a.py", "shop/pricing/b.py"),
                 ("shop/quotes/builder.py", "tools/helper.py")]
        results, unmapped = conformance.compare(components, allowed, edges)
        self.assertEqual({pair: result for pair, (result, _) in results.items()},
                         {("api", "pricing"): "as stated", ("pricing", "storage"): "as stated",
                          ("api", "storage"): "not stated", ("quotes", "pricing"): "not found"})
        self.assertEqual(results[("api", "storage")][1], [("shop/api/serializers.py", "shop/db.py")])
        self.assertEqual(unmapped, ["tools/helper.py"])

    def test_patterns_keep_a_single_star_inside_one_directory(self):
        self.assertTrue(conformance.pattern_regex("app/**/views.py").match("app/views.py"))
        self.assertTrue(conformance.pattern_regex("app/**/views.py").match("app/a/b/views.py"))
        self.assertTrue(conformance.pattern_regex("app/*.py").match("app/x.py"))
        self.assertFalse(conformance.pattern_regex("app/*.py").match("app/a/x.py"))

    def test_cli_reports_counts_and_rejects_an_unknown_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "edges.tsv").write_text("# from\tto\na/x.py\tb/y.py\n")
            (root / "design.json").write_text(json.dumps({"components": {"a": ["a/**"], "b": ["b/**"]}, "allowed": [["b", "a"]]}))
            run = lambda design: subprocess.run([sys.executable, str(SCRIPTS / "design_conformance.py"), str(root / design),
                                                 str(root / "edges.tsv")], capture_output=True, text=True)
            result = run("design.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Relationships: 0 as stated, 1 not stated, 1 not found (from 1 file edges).", result.stdout)
            self.assertIn("a\tb\tnot stated\t1\n\t\t\ta/x.py -> b/y.py", result.stdout)
            (root / "bad.json").write_text(json.dumps({"components": {"a": ["a/**"]}, "allowed": [["a", "z"]]}))
            self.assertEqual(run("bad.json").returncode, 2)


class SpecialCasesTests(Repository):
    def kinds(self, text):
        return {(number, kind) for number, kind, _ in cases.leads(text.splitlines())}

    def test_each_kind_of_lead_is_found_with_its_line(self):
        python = ("def load(path, options):\n"                                       # 1
                  "    try:\n"                                                        # 2
                  "        data = read(path)\n"                                       # 3
                  "    except Exception:\n"                                           # 4
                  "        return {'total': '0.00'}\n"                                # 5
                  "    limit = options.get('limit', 10)\n"                            # 6
                  "    rows = options.get('rows') or []\n"                            # 7
                  "    owner = current.get() or self._default_owner\n"                # 8
                  "    if data is None:\n"                                            # 9
                  "        return\n"                                                  # 10
                  "    if tier is None: return 0\n"                                   # 11
                  "    time.sleep(2)\n"                                               # 12
                  "    if response.status_code == 409:\n"                             # 13
                  "        pass\n"                                                    # 14
                  "    if spec.get('spec_version') == 2:\n"                           # 15
                  "        pass\n"                                                    # 16
                  "    # legacy path kept for old clients\n"                          # 17
                  "    return data  # type: ignore\n")                                # 18
        self.assertEqual(self.kinds(python), {
            (4, "broad error handler"), (4, "error turned into a value or dropped"), (6, "default to a named value"),
            (7, "default to an empty value"), (8, "default to a named value"), (9, "early return on missing"),
            (11, "early return on missing"), (12, "retry or sleep"), (13, "branch on a status code or version"),
            (15, "branch on a status code or version"), (17, "compatibility path"), (18, "suppressed check")})

    def test_words_in_docstrings_and_comments_are_not_the_construct(self):
        quotes = '"' * 3
        python = (f"def f():\n    {quotes}Retry with sleep(2) on the legacy fallback.{quotes}\n"
                  f"    {quotes}\n    status == 404 and a fallback\n    {quotes}\n"
                  "    # we retry once: sleep(1), status == 500\n    return 1\n")
        self.assertEqual(self.kinds(python), set())
        self.assertEqual(self.kinds("if not found:\n    raise Missing()\n"), set(), "failing loudly is not an early return")

    def test_a_narrow_handler_that_reraises_is_not_a_lead(self):
        self.assertEqual(self.kinds("try:\n    run()\nexcept KeyError as error:\n    raise Missing(error) from error\n"), set())
        script = "try {\n  run();\n} catch (e) {\n  console.error(e);\n}\nconst n = input ?? 0;\nconst m = input ?? other;\nif (!user) { return; }\n"
        self.assertEqual(self.kinds(script), {(3, "broad error handler"), (3, "error turned into a value or dropped"),
                                              (6, "default to an empty value"), (7, "default to a named value"),
                                              (8, "early return on missing")})

    def test_report_counts_per_kind_and_leaves_tests_out_by_default(self):
        self.commit({"app/load.py": "try:\n    x()\nexcept:\n    pass\n", "tests/test_load.py": "try:\n    x()\nexcept:\n    pass\n",
                     "README.md": "fallback\n"})
        out = self.run_script("special_cases")
        self.assertIn("Leads to special cases: 2 lines in 1 files.", out)
        self.assertIn("app/load.py:3\texcept:", out)
        self.assertNotIn("tests/test_load.py", out)
        self.assertIn("tests/test_load.py", self.run_script("special_cases", "--tests"))
        self.assertNotIn("## broad error handler", self.run_script("special_cases", "--summary"))

    def test_with_a_base_only_added_lines_are_listed_in_a_commit_or_the_working_tree(self):
        self.commit({"app/load.py": "def load(x):\n    try:\n        return read(x)\n    except Exception:\n        return None\n"})
        base = self.git("rev-parse", "HEAD")
        self.commit({"app/load.py": "def load(x, opts):\n    limit = opts.get('limit') or []\n    try:\n        return read(x)\n"
                                    "    except Exception:\n        return None\n",
                     "app/new.py": "import time\ntime.sleep(1)\n"})
        out = self.run_script("special_cases", "--base", base, "--head", "HEAD")
        self.assertIn(f"on lines added since {base}: 2 lines in 2 files", out)
        self.assertIn("app/load.py:2\tlimit = opts.get('limit') or []", out)
        self.assertIn("app/new.py:2\ttime.sleep(1)", out)
        self.assertNotIn("except Exception", out, "the handler was there before the change")
        self.write({"app/untracked.py": "value = a or {}\n", "app/load.py": "def load(x, opts):\n    return opts.get('k', DEFAULT)\n"})
        out = self.run_script("special_cases", "--base", "HEAD")
        self.assertIn("app/untracked.py:1\tvalue = a or {}", out)
        self.assertIn("app/load.py:2\treturn opts.get('k', DEFAULT)", out)
        self.assertNotIn("time.sleep", out)


class AddedUnitsTests(Repository):
    RUBY_BASE = ("module Shop\n  module Tiers\n    module Base\n      def rate(order)\n        order[:rate]\n      end\n    end\n"
                 "    module Gold\n      extend Base\n      KIND = \"gold\"\n    end\n  end\nend\n")

    def test_ruby_units_with_only_a_constant_are_leads_and_grouped_by_their_base(self):
        self.commit({"lib/tiers.rb": self.RUBY_BASE})
        base = self.git("rev-parse", "HEAD")
        added = ("    module Silver\n      extend Base\n      KIND = \"silver\"\n    end\n"
                 "    module Bronze\n      extend Base\n      KIND = \"bronze\"\n    end\n"
                 "    class Quote < Struct\n      def total(order, rounding: 2, legacy: false)\n        if order[:lines].empty?\n          0\n        end\n      end\n\n"
                 "      def rate(order) = Base.rate(order)\n\n      def empty? = lines.empty?\n    end\n")
        self.commit({"lib/tiers.rb": self.RUBY_BASE.replace("  end\nend\n", added + "  end\nend\n"),
                     "lib/checkout.rb": "puts Shop::Tiers::Quote.new.total(order, rounding: 0)\n"})
        out = self.run_script("added_units", "--base", base, "--head", "HEAD")
        self.assertIn("Leads from", out)
        self.assertIn("Base: Shop::Tiers::Silver, Shop::Tiers::Bronze", out)
        self.assertIn("lib/tiers.rb:12\tShop::Tiers::Silver\t0 methods, 1 constant; extend Base", out)
        self.assertIn("Shop::Tiers::Quote\t3 methods (1 only passes parameters on), 0 constants; Struct", out)
        self.assertIn("lib/tiers.rb:27\tShop::Tiers::Quote.rate\n", out, "a method that hands its parameter to one call")
        self.assertNotIn("Quote.empty?", out, "a method with no parameter is not listed as a wrapper")
        self.assertIn("Shop::Tiers::Quote.total\tlegacy\n", out, "no line sets legacy: by keyword")
        self.assertNotIn("Quote.total\trounding", out, "checkout sets rounding:")
        self.assertNotIn("Shop::Tiers::Gold", out, "Gold was there before the change")
        self.assertNotIn("\tShop\t", out, "a module that only encloses others adds nothing itself")
        self.assertIn("Not looked for:", out, "the output says what no lead clears")

    def test_python_classes_are_parsed_and_a_moved_class_names_where_the_base_held_it(self):
        self.commit({"app/kinds.py": "class Kind:\n    def label(self):\n        if self.code:\n            return self.code\n        return ''\n",
                     "app/old.py": "class Region(Kind):\n    CODE = 'r'\n"})
        base = self.git("rev-parse", "HEAD")
        (self.repo / "app/old.py").unlink()
        self.commit({"app/kinds.py": "class Kind:\n    def label(self):\n        if self.code:\n            return self.code\n        return ''\n\n\n"
                                     "class Region(Kind):\n    CODE = 'r'\n\n\nclass Team(Kind):\n    CODE = 't'\n\n\n"
                                     "class Proxy:\n    def label(self, kind):\n        \"\"\"Doc.\"\"\"\n        return kind.label()\n",
                     "tests/test_kinds.py": "class Fake(Kind):\n    CODE = 'f'\n"})
        out = self.run_script("added_units", "--base", base, "--head", "HEAD")
        self.assertIn("Kind: Region, Team", out)
        self.assertIn("app/kinds.py:8\tRegion\t0 methods, 1 constant; Kind\tthe base holds a unit of this name in app/old.py", out)
        self.assertIn("Proxy\t1 method (1 only passes parameters on), 0 constants", out)
        self.assertNotIn("Fake", out, "test files are left out by default")
        self.assertIn("Fake", self.run_script("added_units", "--base", base, "--head", "HEAD", "--tests"))

    def test_files_wrappers_unset_options_and_single_implementations_are_leads(self):
        self.commit({"kinds/team.py": "KIND = 'team'\n\n\ndef config(entity):\n    return entity if entity.get('kind') == KIND else None\n",
                     "pricing.py": "def total(order):\n    return order['amount']\n"})
        base = self.git("rev-parse", "HEAD")
        self.commit({"kinds/region.py": "KIND = 'region'\n", "kinds/cost.py": "KIND = 'cost'\n",
                     "pricing.py": "def total(order):\n    return order['amount']\n\n\ndef get_total(order):\n    return total(order)\n\n\n"
                                   "def price(order, legacy_mode=False, rounding=2):\n    if legacy_mode:\n        return 0\n"
                                   "    return round(total(order), rounding)\n\n\ndef quote(order):\n    return price(order, rounding=0)\n",
                     "handler.py": "class Handler:\n    def run(self, x):\n        raise NotImplementedError\n\n\n"
                                   "class OnlyHandler(Handler):\n    def run(self, x):\n        if x:\n            return 1\n        return 2\n"})
        out = self.run_script("added_units", "--base", base, "--head", "HEAD")
        self.assertIn("Leads from", out)
        self.assertIn("kinds/: cost.py, region.py", out)
        self.assertIn("kinds/region.py\t(file)\t0 functions, 1 constant", out)
        self.assertNotIn("kinds/team.py", out, "the file was there before the change")
        self.assertIn("pricing.py:5\tget_total\n", out)
        self.assertNotIn("\tquote\n", out, "quote passes a value of its own, so it decides something")
        self.assertIn("pricing.py:9\tprice\tlegacy_mode\n", out)
        self.assertNotIn("price\trounding", out, "quote sets rounding by keyword")
        self.assertIn("handler.py:1\tHandler\textended only at handler.py:6", out)

    def test_a_unit_that_takes_the_name_of_another_is_a_lead(self):
        self.commit({"lib/locker.rb": "class Locker\n  def full? = false\nend\n",
                     "lib/depot/base.rb": "module Depot\n  module Base\n    def zone = 1\n  end\nend\n"})
        base = self.git("rev-parse", "HEAD")
        self.commit({"lib/depot/locker.rb": "module Depot\n  module Locker\n    extend Base\n    KIND = \"locker\"\n  end\nend\n",
                     "lib/depot/more.rb": "module Depot\n  module Base\n    def days = 3\n  end\nend\n"})
        out = self.run_script("added_units", "--base", base, "--head", "HEAD")
        self.assertIn("lib/depot/locker.rb:2\tDepot::Locker\tlib/locker.rb:1 defines Locker", out)
        self.assertNotIn("defines Depot::Base", out, "a unit reopened under its own name is the same unit")

    def test_the_working_tree_counts_untracked_files_and_a_bad_base_exits_2(self):
        self.commit({"app/kinds.py": "class Kind:\n    pass\n"})
        self.write({"app/more.py": "class Zone(Kind):\n    CODE = 'z'\n", "app/broken.py": "class (:\n"})
        out = self.run_script("added_units", "--base", "HEAD")
        self.assertIn("HEAD to the working tree: 1.", out)
        self.assertIn("app/more.py:1\tZone", out)
        self.assertNotIn("extended only", out, "Kind was there before the change")
        self.assertIn("Not parsed: app/broken.py", out)
        result = subprocess.run([sys.executable, str(SCRIPTS / "added_units.py"), "--base", "no-such-commit"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("added_units:", result.stderr)


class FunctionCouplingTests(Repository):
    def test_functions_that_change_together_inside_one_file_are_paired(self):
        body = lambda a, b, c: (f"class Store:\n    def save(self):\n        return {a}\n\n    def load(self):\n        return {b}\n\n"
                                f"def report():\n    return {c}\n")
        self.commit({"app/store.py": body(1, 1, 1)})
        for a, b, c in ((2, 2, 1), (3, 3, 1), (4, 4, 2)):
            self.commit({"app/store.py": body(a, b, c)})
        out = self.run_script("change_coupling", "--functions", "--since", "10 years ago")
        self.assertIn("3\tapp/store.py::save", out)
        self.assertIn("3\t100%\tcode\tsame file\tinside\tnot given\tapp/store.py::load  <->  app/store.py::save", out)
        self.assertNotIn("app/store.py::report  <->", out, "report changed with them only once")
        attributes = SCRIPTS / "function-names.gitattributes"
        history = self.git("-c", f"core.attributesFile={attributes}", "log", "--oneline", "-L", ":load:app/store.py")
        self.assertEqual(len([line for line in history.splitlines() if re.match(r"^[0-9a-f]{7,} ", line)]), 4)


class BreakProbeTests(Repository):
    def test_breaks_are_classified_and_a_focused_miss_is_rerun_under_the_full_suite(self):
        self.commit({"app/__init__.py": "",
                     "app/rates.py": "GOLD = 10\nSILVER = 5\nBRONZE = 1\n",
                     "tests/__init__.py": "",
                     "tests/test_gold.py": "import unittest\nfrom app import rates\n\nclass T(unittest.TestCase):\n    def test_gold(self):\n        self.assertEqual(rates.GOLD, 10)\n",
                     "tests/test_silver.py": "import unittest\nfrom app import rates\n\nclass T(unittest.TestCase):\n    def test_silver(self):\n        self.assertEqual(rates.SILVER, 5)\n"})
        breaks = self.repo / "breaks.tsv"
        breaks.write_text("# name\tpath\tline\treplacement\tfocused command\n"
                          "gold\tapp/rates.py\t1\tGOLD = 11\tpython3 -m unittest tests.test_gold -q\n"
                          "silver\tapp/rates.py\t2\tSILVER = 6\tpython3 -m unittest tests.test_gold -q\n"
                          "bronze\tapp/rates.py\t3\tBRONZE = 2\tpython3 -m unittest tests.test_gold -q\n")
        out = self.run_script("break_probe", str(breaks), "--full", "python3 -m unittest discover -s tests -q", "--out", str(self.repo / "runs"))
        self.assertIn("focused red\tgold\tapp/rates.py:1", out)
        self.assertIn("full red\tsilver\tapp/rates.py:2", out)
        self.assertIn("green\tbronze\tapp/rates.py:3\tBRONZE = 1\tno test protects it", out)
        self.assertIn("1 of 3 breaks left every test green", out)
        self.assertEqual((self.repo / "app/rates.py").read_text(), "GOLD = 10\nSILVER = 5\nBRONZE = 1\n", "the checkout is never touched")
        self.assertEqual(len(self.git("worktree", "list").splitlines()), 1, "the scratch worktree is removed")
        self.assertTrue((self.repo / "runs/02-full.log").exists())

    LOCK_TEST = "import unittest\nfrom app import rates\n\nclass T(unittest.TestCase):\n    def test_gold(self):\n        self.assertEqual(rates.GOLD, 10)\n"

    def lock_test_left_uncommitted(self):
        self.commit({"app/__init__.py": "", "app/rates.py": "GOLD = 10\n", "tests/__init__.py": "",
                     "tests/test_helper.py": "VALUE = 1\n"})
        self.write({"tests/test_lock.py": self.LOCK_TEST, "tests/test_helper.py": "VALUE = 2\n"})  # a new file and an edited one
        breaks = self.repo / "breaks.tsv"
        breaks.write_text("gold\tapp/rates.py\t1\tGOLD = 11\tpython3 -m unittest tests.test_lock -q\n")
        return [sys.executable, str(SCRIPTS / "break_probe.py"), str(breaks), "--full", "python3 -m unittest discover -s tests -q",
                "--out", str(self.repo / "runs")]

    def test_a_focused_command_that_fails_before_the_break_is_not_a_pin(self):
        command = self.lock_test_left_uncommitted()
        result = subprocess.run(command, cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("red before the break\tgold\tapp/rates.py:1", result.stdout)
        self.assertNotIn("focused red", result.stdout, "the worktree of HEAD has no lock test, so its failure says nothing")
        self.assertTrue((self.repo / "runs/control-01.log").exists())

    def test_a_full_command_that_fails_before_the_break_cannot_report_a_pin(self):
        self.commit({"app/__init__.py": "", "app/rates.py": "GOLD = 10\nSILVER = 5\n", "tests/__init__.py": "",
                     "tests/test_gold.py": self.LOCK_TEST,
                     "tests/test_known_failure.py": "import unittest\n\nclass T(unittest.TestCase):\n    def test_fails(self):\n        self.fail('fails before any break')\n"})
        breaks = self.repo / "breaks.tsv"
        breaks.write_text("silver\tapp/rates.py\t2\tSILVER = 6\tpython3 -m unittest tests.test_gold -q\n")
        result = subprocess.run([sys.executable, str(SCRIPTS / "break_probe.py"), str(breaks), "--full", "python3 -m unittest discover -s tests -q",
                                 "--out", str(self.repo / "runs")], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("full red before the break\tsilver\tapp/rates.py:2", result.stdout)
        self.assertNotIn("full red\tsilver", result.stdout, "a suite that fails unbroken would call every break pinned")
        self.assertTrue((self.repo / "runs/control-full.log").exists())
        self.assertEqual((self.repo / "app/rates.py").read_text(), "GOLD = 10\nSILVER = 5\n")

    def test_local_changes_bring_an_uncommitted_lock_test_into_the_scratch_worktree(self):
        command = self.lock_test_left_uncommitted()
        result = subprocess.run(command + ["--with-local-changes"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("focused red\tgold\tapp/rates.py:1", result.stdout)
        self.assertIn("with the checkout's uncommitted changes", result.stdout)
        self.assertEqual((self.repo / "app/rates.py").read_text(), "GOLD = 10\n", "the checkout is never touched")
        self.assertEqual([line.strip() for line in self.git("status", "--short").splitlines()],
                         ["M tests/test_helper.py", "?? breaks.tsv", "?? runs/", "?? tests/test_lock.py"], "the checkout keeps its changes")


    # A timed-out command gives no verdict: it is neither a test that caught the break nor one that stayed green.
    def probe(self, breaks, full):
        path = self.repo / "breaks.tsv"
        path.write_text(breaks)
        return subprocess.run([sys.executable, str(SCRIPTS / "break_probe.py"), str(path), "--full", full, "--timeout", "1",
                               "--out", str(self.repo / "runs")], cwd=self.repo, capture_output=True, text=True)

    def assert_no_survivor(self, marker):
        """No process the timed-out command started is still running; `marker` is a sleep length no other test uses."""
        if not shutil.which("pgrep"):
            self.skipTest("pgrep is not installed")
        time.sleep(0.5)
        found = subprocess.run(["pgrep", "-f", marker], capture_output=True, text=True)
        self.assertEqual(found.stdout.strip(), "", f"a process started by the command outlived its timeout: {marker}")

    def once_slow(self, marker):
        """A command that is slow the first time it runs and quick after, through a flag outside the worktree."""
        flags = tempfile.TemporaryDirectory()
        self.addCleanup(flags.cleanup)
        flag = Path(flags.name) / "ran"
        return f"if [ -e {flag} ]; then true; else touch {flag}; sleep {marker}; fi"

    def test_a_focused_command_that_times_out_under_the_break_gives_no_verdict(self):
        self.commit({"a.txt": "original\n"})
        result = self.probe("slow focused\ta.txt\t1\tchanged\tgrep -q changed a.txt && sleep 5.41 || true\n", "true")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("timed out\tslow focused\ta.txt:1\toriginal\tno verdict: the command passed --timeout 1 s", result.stdout)
        self.assertNotIn("focused red", result.stdout)
        self.assertIn("1 of 1 breaks timed out; their rows carry no verdict.", result.stdout)
        self.assertIn("timed out after 1 s", (self.repo / "runs/01-focused.log").read_text())
        self.assert_no_survivor("sleep 5.41")

    def test_a_full_command_that_times_out_under_the_break_gives_no_verdict(self):
        self.commit({"a.txt": "original\n"})
        result = self.probe("slow full\ta.txt\t1\tchanged\ttrue\n", "grep -q changed a.txt && sleep 5.42 || true")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("timed out\tslow full\ta.txt:1", result.stdout)
        self.assertNotIn("full red", result.stdout)
        self.assert_no_survivor("sleep 5.42")

    def test_a_full_control_that_times_out_is_retried_by_the_next_break(self):
        self.commit({"a.txt": "one\ntwo\n"})
        result = self.probe("first\ta.txt\t1\tchanged\ttrue\nsecond\ta.txt\t2\tchanged\ttrue\n", self.once_slow("5.43"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("timed out before the break\tfirst\ta.txt:1\tone\tno verdict: the command passed --timeout 1 s "
                      "on the unbroken worktree", result.stdout)
        self.assertIn("green\tsecond\ta.txt:2", result.stdout, "the next break runs the control again, not its cached timeout")
        self.assertNotIn("full red before the break", result.stdout)
        self.assert_no_survivor("sleep 5.43")

    def test_a_focused_control_that_times_out_is_retried_by_the_next_break(self):
        self.commit({"a.txt": "one\ntwo\n"})
        command = self.once_slow("5.44")
        result = self.probe(f"first\ta.txt\t1\tchanged\t{command}\nsecond\ta.txt\t2\tchanged\t{command}\n", "true")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("timed out before the break\tfirst\ta.txt:1", result.stdout)
        self.assertNotIn("red before the break\tfirst", result.stdout.replace("timed out before the break", ""))
        self.assertIn("green\tsecond\ta.txt:2", result.stdout)
        self.assert_no_survivor("sleep 5.44")

class SharedDataTests(Repository):
    RUBY = {
        "lib/pricing.rb": ("def apply!(order)\n"
                           "  subtotal = order[:total] || 0\n"
                           "  order[:discount] = subtotal * RATES.fetch(order[:customer][:tier], 0)\n"
                           "  order[:total] = subtotal - order[:discount]\n"
                           "end\n"),
        "lib/shipping.rb": "def add!(order)\n  order[:total] = order[:total] + 4.9\n  order.merge!(shipping: 4.9, \"carrier\" => \"post\")\nend\n",
        "lib/notifier.rb": "def receipt(order)\n  currency = order.fetch(:currency, \"EUR\")\n  \"#{order[:total]} #{currency} #{order.dig(:customer, :email)}\"\nend\n",
        "lib/report.rb": "class Report\n  @@totals = Hash.new(0)\n  def record(order)\n    order.fetch(:currency, \"USD\")\n    $last = order\n  end\nend\n",
    }

    def test_key_uses_tell_writes_reads_and_defaults_apart(self):
        uses = shared.key_uses(self.RUBY["lib/pricing.rb"].splitlines())
        self.assertIn((2, "total", "default", "0"), uses)
        self.assertIn((3, "discount", "write", None), uses)
        self.assertIn((3, "tier", "read", None), uses)  # the default belongs to RATES.fetch, whose key is an expression
        self.assertIn((3, "customer", "read", None), uses)
        self.assertIn((4, "total", "write", None), uses)
        self.assertIn((4, "discount", "read", None), uses)
        self.assertNotIn((4, "total", "read", None), uses, "the written key is not also a read")
        python = shared.key_uses(['x = data.get("limit", 10)', 'data["limit"] = 5', "y = data['mode']", "data.setdefault('mode', 'a')"])
        self.assertEqual(python, [(1, "limit", "default", "10"), (2, "limit", "write", None), (3, "mode", "read", None), (4, "mode", "write", None)])

    def test_ledger_names_keys_no_one_place_declares(self):
        self.commit(self.RUBY)
        out = self.run_script("shared_data")
        self.assertIn("lib/report.rb:2\t@@totals = Hash.new(0)", out)
        self.assertIn("lib/report.rb:5\t$last = order", out)
        self.assertIn("total\twritten in 2 files; read with a default at 1 site; written in one file, read in another", out)
        self.assertIn('currency\tread with a default at 2 sites; defaults differ: "EUR" | "USD"', out)
        self.assertIn("shipping\twritten, never read here", out)
        self.assertIn("carrier\twritten, never read here", out)
        self.assertNotIn("\nemail\t", out, "a key that is only read gives no sign")

    def test_with_a_base_only_the_state_and_keys_of_added_lines_are_listed(self):
        self.commit({"app/rates.rb": "module Rates\n  def self.for(order)\n    order[:weight] || 0\n  end\nend\n",
                     "app/old.rb": "$registry = {}\nopts[:legacy] ||= true\n"})
        base = self.git("rev-parse", "HEAD")
        self.commit({"app/rates.rb": "module Rates\n  def self.for(order)\n    @prices ||= {}\n    order[:total] = order[:weight] || 0\n  end\nend\n",
                     "app/labels.rb": "def label(order) = order[:total] || 'none'\n"})
        out = self.run_script("shared_data", "--base", base, "--head", "HEAD")
        self.assertIn(f"on lines added since {base}: 1 lines", out)
        self.assertIn("app/rates.rb:3\t@prices ||= {}", out)
        self.assertNotIn("$registry", out, "state the base already held is not listed")
        self.assertIn("total\t", out)
        self.assertNotIn("legacy\t", out, "a key the change does not touch is not listed")
        self.write({"app/more.rb": "$cache = {}\n"})
        self.assertIn("app/more.rb:1\t$cache = {}", self.run_script("shared_data", "--base", "HEAD"))

    def test_state_leads_cover_python_and_javascript_and_skip_comments(self):
        python = ["_cache = {}", "def f():", "    global counter", "    # $x = 1 and @@y = 2", "LIMIT = 10"]
        self.assertEqual([(n, kind) for n, kind, _ in shared.state_leads(python)],
                         [(1, "module-level collection"), (1, "memo or cache"), (3, "global or class-level variable")])
        script = ["let registry = new Map();", "window.app = {};", "const fixed = 1;", "private static int count = 0;", "private static final int MAX = 3;"]
        self.assertEqual([(n, kind) for n, kind, _ in shared.state_leads(script)],
                         [(1, "module-level collection"), (2, "global or class-level variable"), (4, "global or class-level variable")])


class AddedValuesTests(Repository):
    def test_values_are_words_in_quotes_symbols_word_lists_and_numbers(self):
        self.assertEqual(values.values('KINDS = %w[standard express] + [:locker, "pick-up"]; rate = 0.15 if n > 100'),
                         {"standard", "express", "locker", "pick-up", "0.15", "100"})
        self.assertEqual(values.values("  # 'express' in a comment"), set())
        self.assertEqual(values.values('x = {kind: "ab", "name" => true, Foo::Bar => 12}'), set(), "short, common, and non-literal words")

    def test_a_value_added_in_two_files_is_listed_with_the_files_that_hold_it(self):
        self.commit({"app/pricing.py": "RATES = {'gold': 0.10}\n", "app/quotes.py": "TIERS = ('gold',)\n", "app/other.py": "x = 1\n"})
        base = self.git("rev-parse", "HEAD")
        self.commit({"app/pricing.py": "RATES = {'gold': 0.10, 'platinum': 0.15}\n", "app/quotes.py": "TIERS = ('gold', 'platinum')\n",
                     "app/other.py": "x = 1\nlabel = 'once'\n", "tests/test_pricing.py": "assert rate('platinum') == 0.15\n"})
        out = self.run_script("added_values", "--base", base, "--head", "HEAD")
        self.assertIn("platinum\tadded in 2 files; 2 files hold it at the head", out)
        self.assertIn("app/pricing.py:1, app/quotes.py:1", out)
        self.assertNotIn("once", out, "a value added in one file is not listed")
        self.assertNotIn("0.15", out, "the rate is added in one source file; the test file is left out")
        self.assertIn("0.15\tadded in 2 files", self.run_script("added_values", "--base", base, "--head", "HEAD", "--tests"))
        self.write({"app/new.py": "KIND = 'silver'\n", "app/quotes.py": "TIERS = ('gold', 'platinum', 'silver')\n"})
        self.assertIn("silver\tadded in 2 files", self.run_script("added_values", "--base", "HEAD"))
        result = subprocess.run([sys.executable, str(SCRIPTS / "added_values.py"), "--base", "no-such-commit"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


class TestsForLineTests(unittest.TestCase):
    def data(self, directory, contexts=True):
        """A coverage.py data file with the three tables the script reads."""
        path = Path(directory) / ".coverage"
        database = sqlite3.connect(path)
        database.executescript("create table file (id integer primary key, path text);"
                               "create table context (id integer primary key, context text);"
                               "create table line_bits (file_id integer, context_id integer, numbits blob);"
                               "create table arc (file_id integer, context_id integer, fromno integer, tono integer);")
        database.execute("insert into file values (1, '/repo/shop/pricing/discounts.py')")
        database.executemany("insert into context values (?, ?)", [(1, ""), (2, "tests/test_a.py::test_gold|run"), (3, "tests/test_a.py::test_guest|run")]
                             if contexts else [(1, "")])
        bits = lambda *lines: bytes(sum(1 << (line % 8) for line in lines if line // 8 == index) for index in range(max(lines) // 8 + 1))
        database.executemany("insert into line_bits values (1, ?, ?)", [(1, bits(1, 12, 20)), (2, bits(12, 13)), (3, bits(20))]
                             if contexts else [(1, bits(12))])
        database.commit()
        database.close()
        return path

    def test_lines_come_out_of_the_numbits_blob(self):
        self.assertEqual(tests_for_line.lines_of(bytes([0b00000010, 0b00010000])), {1, 12})

    def test_tests_are_listed_per_line_and_an_unexecuted_line_has_none(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(SCRIPTS / "tests_for_line.py"), str(self.data(directory)),
                                     "pricing/discounts.py:12", "discounts.py:20", "discounts.py:99"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pricing/discounts.py:12\t1 tests\n\ttests/test_a.py::test_gold|run", result.stdout)
            self.assertIn("discounts.py:20\t1 tests\n\ttests/test_a.py::test_guest|run", result.stdout)
            self.assertIn("discounts.py:99\t0 tests", result.stdout)

    def test_data_without_per_test_contexts_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(SCRIPTS / "tests_for_line.py"), str(self.data(directory, contexts=False)),
                                     "discounts.py:12"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("no per-test contexts", result.stderr)


class PinnedLinesTests(Repository):
    def test_each_pin_prints_its_source_and_a_wrong_pin_is_missing(self):
        self.commit({"shop/pricing.py": "RATES = {}\n\ndef total(amount):\n    return amount\n"})
        sha = self.git("rev-parse", "HEAD")
        note = self.repo / "notes" / "map.md"
        note.parent.mkdir()
        note.write_text("# Map\n\n"
                        "The total is decided at [pricing.py:3](../shop/pricing.py#L3-L4).\n"
                        f"Rates live at [pricing.py:1](https://example.invalid/acme/shop/blob/{sha}/shop/pricing.py#L1).\n"
                        "```text\n[ignored](../shop/pricing.py#L1)\n```\n"
                        "A wrong pin: [pricing.py:40](../shop/pricing.py#L40).\n")
        result = subprocess.run([sys.executable, str(SCRIPTS / "pinned_lines.py"), str(note), "--repo", str(self.repo)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("note:3\t[pricing.py:3]\tpricing.py:3-4\tdef total(amount): ⏎ return amount", result.stdout)
        self.assertIn("note:4\t[pricing.py:1]\tpricing.py:1\tRATES = {}", result.stdout)
        self.assertIn("note:8\t[pricing.py:40]\tpricing.py:40\tMISSING", result.stdout)
        self.assertNotIn("ignored", result.stdout)
        self.assertIn("3 pins, 1 missing", result.stderr)


if __name__ == "__main__":
    unittest.main()

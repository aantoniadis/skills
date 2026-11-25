"""The four untangle scripts: change coupling from history, import edges, the stated design against the
edges, and the leads to special cases. Each prints leads; the tests pin what they find and what they leave out."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/untangle/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coupling, imports, conformance, cases = (load(name) for name in
                                         ("change_coupling", "import_edges", "design_conformance", "special_cases"))


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

    def test_report_marks_pairs_without_a_dependency_and_leaves_out_deleted_and_generated_files(self):
        for round_ in range(3):
            self.commit({"shop/pricing/discounts.py": f"RATE = {round_}\n", "shop/quotes/builder.py": f"RATE = {round_}\n",
                         "shop/api/views.py": f"from shop.pricing import discounts  # {round_}\n",
                         "gone.py": f"{round_}\n", "package-lock.json": f"{round_}\n"})
        self.git("rm", "-q", "gone.py")
        self.git("commit", "-q", "-m", "remove")
        (self.repo / "edges.tsv").write_text("# from\tto\nshop/api/views.py\tshop/pricing/discounts.py\n")
        out = self.run_script("change_coupling", "--edges", "edges.tsv", "--since", "10 years ago")
        self.assertIn("History: 4 commits", out)
        self.assertIn("3\t100%\tdifferent\tnone found\tshop/pricing/discounts.py  <->  shop/quotes/builder.py", out)
        self.assertIn("3\t100%\tdifferent\tyes\tshop/api/views.py  <->  shop/pricing/discounts.py", out)
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
        })
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
    def test_each_kind_of_lead_is_found_with_its_line(self):
        python = ("def load(path, options):\n"
                  "    try:\n"
                  "        data = read(path)\n"
                  "    except Exception:\n"
                  "        return None\n"
                  "    limit = options.get('limit', 10)\n"
                  "    if data is None: return\n"
                  "    time.sleep(2)  # retry once\n"
                  "    # legacy path kept for old clients\n"
                  "    return data  # type: ignore\n")
        found = {(number, kind) for number, kind, _ in cases.leads(python.splitlines())}
        self.assertEqual(found, {(4, "broad error handler"), (4, "swallowed error"), (6, "default when missing"),
                                 (7, "early return on missing"), (8, "retry or sleep"), (9, "compatibility path"),
                                 (10, "suppressed check")})

    def test_a_narrow_handler_that_reraises_is_not_a_lead(self):
        python = "try:\n    run()\nexcept KeyError as error:\n    raise Missing(error) from error\n"
        self.assertEqual(cases.leads(python.splitlines()), [])
        script = "try {\n  run();\n} catch (e) {\n  console.error(e);\n}\nconst n = input ?? 0;\n"
        self.assertEqual({(number, kind) for number, kind, _ in cases.leads(script.splitlines())},
                         {(3, "broad error handler"), (3, "swallowed error"), (6, "default when missing")})

    def test_report_counts_per_kind_and_leaves_tests_out_by_default(self):
        self.commit({"app/load.py": "try:\n    x()\nexcept:\n    pass\n", "tests/test_load.py": "try:\n    x()\nexcept:\n    pass\n",
                     "README.md": "fallback\n"})
        out = self.run_script("special_cases")
        self.assertIn("Leads to special cases: 2 lines in 1 files.", out)
        self.assertIn("app/load.py:3\texcept:", out)
        self.assertNotIn("tests/test_load.py", out)
        self.assertIn("tests/test_load.py", self.run_script("special_cases", "--tests"))


if __name__ == "__main__":
    unittest.main()

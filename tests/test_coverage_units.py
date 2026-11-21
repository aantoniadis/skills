"""coverage_units.py seeds one unit per changed symbol with its classes and consumers, and checks dispositions."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/find-bugs/scripts/coverage_units.py"
CLASSES = ("boundary", "errors", "state", "consumers", "concurrency", "normalization", "cost", "compatibility")


class CoverageUnitsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "diff.mnemonicPrefix", "true")
        (self.repo / "app.py").write_text(
            "import os\n\n\ndef total(items):\n    return sum(items)\n\n\ndef unused():\n    return 0\n")
        (self.repo / "caller.py").write_text("from app import total\n\n\ndef report():\n    return str(total([1]))\n")
        (self.repo / "test_app.py").write_text("def test_total():\n    assert total([1]) == 1\n")
        self.base = self.commit()

    def git(self, *args):
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        return subprocess.check_output(["git", "-C", str(self.repo), *args], env=env, text=True).strip()

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "fixture")
        return self.git("rev-parse", "HEAD")

    def run_script(self, *args, code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stderr or result.stdout)
        return result.stdout

    def seed(self, *args):
        return json.loads(self.run_script("--base", self.base, "--head", "HEAD", *args))

    def change(self):
        (self.repo / "app.py").write_text(
            "import os\n\n\ndef total(items):\n    return sum(items) / len(items)\n\n\ndef unused():\n    return 0\n")
        return self.commit()

    def test_one_unit_per_changed_symbol_with_its_lines_and_classes(self):
        head = self.change()
        ledger = json.loads(self.run_script("--base", self.base, "--head", head))
        unit = next(unit for unit in ledger["units"] if unit["id"] == "app.py::total")
        self.assertEqual(unit["change"], "modified")
        self.assertEqual(unit["lines"], [[5, 5]])
        self.assertEqual(unit["status"], "planned")
        self.assertEqual(unit["sweep"], {})
        self.assertEqual(ledger["classes"], list(CLASSES) + ["text"])
        self.assertEqual(unit["classes"], list(CLASSES))
        self.assertEqual([check["name"] for check in ledger["change_checks"]],
                         ["untested lines", "weakened checks", "dependency compatibility", "static deltas",
                          "history and review context", "caller hypotheses"])
        self.assertEqual(ledger["gap_check"]["status"], "not run")
        self.assertEqual(ledger["pins"]["base_sha"], self.base)
        self.assertEqual(ledger["pins"]["head_sha"], head)

    def test_consumers_outside_the_change_are_listed(self):
        (self.repo / "README.md").write_text("Run total to add the items.\n")
        self.change()
        unit = next(unit for unit in self.seed()["units"] if unit["id"] == "app.py::total")
        self.assertEqual(unit["consumers"], ["caller.py", "test_app.py"])
        self.assertFalse(unit["consumers_truncated"])

    def test_consumers_rank_the_nearest_directory_first_and_skip_vendored_files(self):
        (self.repo / "vendor").mkdir()
        (self.repo / "vendor" / "bundled.min.js").write_text("function total(){}\n")
        (self.repo / "node_modules").mkdir()
        (self.repo / "node_modules" / "dep.py").write_text("def total():\n    return 0\n")
        (self.repo / "zz.py").write_text("from app import total\n")
        self.base = self.commit()
        self.change()
        unit = next(unit for unit in self.seed()["units"] if unit["id"] == "app.py::total")
        self.assertEqual(unit["consumers"], ["caller.py", "test_app.py", "zz.py"])

    def test_prose_and_configuration_get_one_text_unit_per_file(self):
        (self.repo / "README.md").write_text("# Title\n\nOne paragraph.\n\nAnother paragraph.\n")
        (self.repo / "config.json").write_text('{"threshold": 1}\n')
        self.commit()
        units = {unit["id"]: unit for unit in self.seed()["units"]}
        self.assertEqual(units["README.md::file"]["classes"], ["text"])
        self.assertEqual(units["config.json::file"]["classes"], ["text"])
        self.assertNotIn("README.md::hunk-1", units)

    def test_check_accepts_a_text_unit_with_one_clause(self):
        (self.repo / "README.md").write_text("# Title\n\nOne paragraph.\n")
        self.commit()
        ledger = self.seed()
        unit = ledger["units"][0]
        unit.update(status="closed", reviewed=["README.md"], sweep={"text": "prose only; no consumer reads it"})
        for check in ledger["change_checks"]:
            check.update(status="not applicable", note="a prose-only change")
        ledger["gap_check"] = {"status": "clean", "note": "a fresh reader accepted no gap"}
        path = self.repo / "text.json"
        path.write_text(json.dumps(ledger))
        self.assertIn("Every unit has a disposition", self.run_script("--check", str(path)))

    def test_module_level_change_gets_a_hunk_unit(self):
        (self.repo / "app.py").write_text(
            "import os\nimport sys\n\n\ndef total(items):\n    return sum(items)\n\n\ndef unused():\n    return 0\n")
        self.commit()
        ids = [unit["id"] for unit in self.seed()["units"]]
        self.assertIn("app.py::hunk-1", ids)
        self.assertNotIn("app.py::total", ids)

    def test_deleted_symbol_is_resolved_from_the_base(self):
        (self.repo / "app.py").write_text("import os\n\n\ndef total(items):\n    return sum(items)\n")
        self.commit()
        unit = next(unit for unit in self.seed()["units"] if unit["id"] == "app.py::unused")
        self.assertEqual(unit["change"], "deleted")
        self.assertEqual(unit["removed_lines"], [[8, 9]])
        self.assertEqual(unit["lines"], [])

    def test_added_file_units_are_added(self):
        (self.repo / "new.py").write_text("def fresh():\n    return 1\n")
        self.commit()
        unit = next(unit for unit in self.seed()["units"] if unit["id"] == "new.py::fresh")
        self.assertEqual(unit["change"], "added")

    def test_blank_only_change_keeps_one_unit_for_the_file(self):
        (self.repo / "app.py").write_text(
            "import os\n\n\ndef total(items):\n    return sum(items)\n\n\ndef unused():\n    return 0\n\n")
        self.commit()
        units = self.seed()["units"]
        self.assertEqual([unit["id"] for unit in units], ["app.py::hunk-1"])

    def test_coarse_merges_units_per_file(self):
        (self.repo / "caller.py").write_text("from app import total\n\n\ndef report():\n    return str(total([]))\n")
        self.change()
        ledger = self.seed("--coarse")
        self.assertEqual(ledger["pins"]["granularity"], "file")
        self.assertEqual([unit["id"] for unit in ledger["units"]], ["app.py::file", "caller.py::file"])
        self.assertEqual(next(unit for unit in ledger["units"] if unit["path"] == "app.py")["consumers"], ["test_app.py"])

    def test_path_under_a_directory_named_like_a_diff_prefix(self):
        (self.repo / "b").mkdir()
        (self.repo / "b" / "mod.py").write_text("def kept():\n    return 1\n")
        self.commit()
        unit = next(unit for unit in self.seed()["units"] if unit["symbol"] == "kept")
        self.assertEqual(unit["id"], "b/mod.py::kept")
        self.assertEqual(unit["path"], "b/mod.py")

    def test_working_tree_includes_unstaged_and_untracked(self):
        (self.repo / "app.py").write_text(
            "import os\n\n\ndef total(items):\n    return sum(items) + 1\n\n\ndef unused():\n    return 0\n")
        (self.repo / "extra.py").write_text("def added():\n    return 2\n")
        ledger = json.loads(self.run_script())
        self.assertEqual(ledger["pins"]["base"], "HEAD (working tree)")
        self.assertEqual({unit["id"] for unit in ledger["units"]}, {"app.py::total", "extra.py::added"})

    def test_same_pins_seed_the_same_ledger(self):
        self.change()
        self.assertEqual(self.run_script("--base", self.base, "--head", "HEAD"),
                         self.run_script("--base", self.base, "--head", "HEAD"))

    def test_prior_carries_dispositions_as_leads_and_gaps_as_work(self):
        self.change()
        first = self.seed()
        path = self.repo / "ledger.json"
        first["units"][0]["status"] = "deferred"
        first["units"][0]["reason"] = "no time in this pass"
        path.write_text(json.dumps(first))
        again = json.loads(self.run_script("--base", self.base, "--head", "HEAD", "--prior", str(path)))
        carried = next(unit for unit in again["units"] if unit["id"] == first["units"][0]["id"])
        self.assertEqual(carried["status"], "planned")
        self.assertEqual(carried["sweep"], {})
        self.assertTrue(carried["prior"]["source_unchanged"])
        self.assertEqual(carried["prior"]["disposition"], "deferred")
        self.assertEqual(again["prior_gaps"], [{"id": carried["id"], "reason": "no time in this pass"}])
        (self.repo / "app.py").write_text(
            "import os\n\n\ndef total(items):\n    return sum(items) / max(len(items), 1)\n\n\ndef unused():\n    return 0\n")
        self.commit()
        changed = json.loads(self.run_script("--base", self.base, "--head", "HEAD", "--prior", str(path)))
        self.assertFalse(next(unit for unit in changed["units"] if unit["id"] == "app.py::total")["prior"]["source_unchanged"])

    def closed_ledger(self):
        ledger = self.seed()
        for unit in ledger["units"]:
            unit.update(status="closed", reviewed=[unit["path"]],
                        sweep={name: f"{name}: read {unit['path']}:{unit['lines'] or unit['removed_lines']}" for name in CLASSES})
        for check in ledger["change_checks"]:
            check.update(status="done", note="ran and read the result")
        ledger["gap_check"] = {"status": "clean", "note": "a fresh reader accepted no gap"}
        return ledger

    def test_check_reports_a_fresh_ledger_as_incomplete(self):
        path = self.repo / "fresh.json"
        self.change()
        path.write_text(json.dumps(self.seed()))
        out = self.run_script("--check", str(path), code=1)
        self.assertIn("Incomplete coverage", out)
        self.assertIn("app.py::total: status is 'planned', not a disposition", out)
        self.assertIn("gap check: no result and note", out)

    def test_check_accepts_a_full_sweep_and_lists_gaps(self):
        self.change()
        ledger = self.closed_ledger()
        ledger["units"][0].update(status="blocked", reason="the caller needs a service this checkout cannot run",
                                  unresolved=["which callers reach it"])
        path = self.repo / "closed.json"
        path.write_text(json.dumps(ledger))
        out = self.run_script("--check", str(path))
        self.assertIn("Every unit has a disposition", out)
        self.assertIn("Gaps to state in the delivery (1)", out)
        self.assertIn("blocked — the caller needs a service", out)

    def test_check_rejects_a_missing_class_clause_and_a_reasonless_gap(self):
        self.change()
        (self.repo / "caller.py").write_text("from app import total\n\n\ndef report():\n    return str(total([]))\n")
        self.commit()
        ledger = self.closed_ledger()
        unit = next(unit for unit in ledger["units"] if unit["id"] == "app.py::total")
        del unit["sweep"]["concurrency"]
        next(unit for unit in ledger["units"] if unit["id"] == "caller.py::report").update(status="deferred", reason="")
        path = self.repo / "partial.json"
        path.write_text(json.dumps(ledger))
        out = self.run_script("--check", str(path), code=1)
        self.assertIn("app.py::total: no sweep clause for concurrency", out)
        self.assertIn("caller.py::report: deferred without a reason", out)

    def test_check_rejects_a_candidate_without_a_finding(self):
        self.change()
        ledger = self.closed_ledger()
        next(unit for unit in ledger["units"] if unit["id"] == "app.py::total")["status"] = "candidate"
        path = self.repo / "candidate.json"
        path.write_text(json.dumps(ledger))
        self.assertIn("candidate without a finding", self.run_script("--check", str(path), code=1))

    def test_check_rejects_worked_gaps_without_a_clean_pass(self):
        self.change()
        ledger = self.closed_ledger()
        ledger["gap_check"] = {"status": "worked", "note": "pass 1 proposed 6 gaps; all worked; second pass not run"}
        path = self.repo / "worked.json"
        path.write_text(json.dumps(ledger))
        self.assertIn("gap check: gaps were worked, but no later pass accepted nothing",
                      self.run_script("--check", str(path), code=1))

    def test_bad_ref_exits_2(self):
        self.run_script("--base", "nope", "--head", "HEAD", code=2)

    def test_missing_ledger_exits_2(self):
        self.run_script("--check", str(self.repo / "absent.json"), code=2)


if __name__ == "__main__":
    unittest.main()

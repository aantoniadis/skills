import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eval_run", ROOT / "evals/run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class EvalRunnerTests(unittest.TestCase):
    def test_case_graders_parse_and_grade_without_a_judge(self):
        case = run.load_case(ROOT / "evals/find-bugs-outside-the-change")
        graders = [g for g in case["graders"] if g[1]["type"] != "llm"]
        final = "## Defects\n\n1. x\n\n## Outside the change\n\n1. stale index"
        calls = [("Edit", '{"file_path": "/w/.scratch/r/head/notes/index.py"}'), ("Bash", '{"command": "git diff"}')]
        result = run.grade(graders, final, "git diff main", calls, [], "unused")
        self.assertTrue(all(r["passed"] for r in result.values()), result)
        # The checkout grader reads file contents, so an edit through any tool, Bash heredocs included, trips it.
        result = run.grade(graders, "## Defects", "sed -i 's/a/b/' notes/index.py", calls, [], "unused",
                           changed=["notes/index.py"])
        self.assertEqual({k for k, r in result.items() if not r["passed"]},
                         {"checkout-untouched", "no-sed-on-source", "outside-section"})
        self.assertTrue(run.grade(graders, final, "", [], [], "", changed=[".scratch/r/probe.py"])["checkout-untouched"]["passed"])

    def test_contract_pattern_unescapes_and_file_glob_sees_only_new_files(self):
        case = run.load_case(ROOT / "evals/plan-change-tested-contract")
        table = [g for g in case["graders"] if g[0] == "contract-table"]
        self.assertTrue(run.grade(table, "", "| Clause | Seam | Status | Evidence |", [], [], "")["contract-table"]["passed"])
        case = run.load_case(ROOT / "evals/pr-review-guide-fresh-report")
        report = [g for g in case["graders"] if g[0] == "new-report-written"]
        self.assertTrue(run.grade(report, "", "", [], [".scratch/x/report.md"], "")["new-report-written"]["passed"])
        self.assertFalse(run.grade(report, "", "", [], [], "")["new-report-written"]["passed"])


if __name__ == "__main__":
    unittest.main()

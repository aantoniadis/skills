"""workflow_state.py reports the Git position and classifies our skills' notes by their template markers."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/whats-next/scripts/workflow_state.py"
TEMPLATES = {  # kind -> the template or fixture every real artifact is filled from
    "understanding note (explain)": ROOT / "skills/explain/references/understanding-template.md",
    "plan (plan-change)": ROOT / "skills/plan-change/references/plan-template.md",
    "diagnosis note (fix-bug)": ROOT / "tests/fixtures/diagnosis/diagnosis.md",
    "PR review guide (pr-review-guide)": ROOT / "skills/pr-review-guide/references/report-template.md",
    "acceptance report (check-acceptance)": ROOT / "skills/check-acceptance/references/report-template.md",
}


def run(*args, cwd, env=None):
    result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    return result.stdout


class WorkflowStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {**os.environ, "XDG_STATE_HOME": str(self.root / "state")}
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["bash", "-c", "git init -q -b main && echo a > a && git add . && git -c user.email=t@t -c user.name=t commit -qm init"
                        " && git checkout -q -b feat/x && echo b > b && git add b && git -c user.email=t@t -c user.name=t commit -qm two && echo c > c"],
                       cwd=self.repo, check=True)

    def test_git_position_and_classified_notes(self):
        for index, (kind, template) in enumerate(TEMPLATES.items()):
            target = self.repo / (".scratch" if index % 2 else "docs") / f"n{index}" / template.name
            target.parent.mkdir(parents=True)
            shutil.copy(template, target)
        (self.repo / "docs/plain.md").write_text("# Plain\n\nNo marker here.\n")
        out = run(str(self.repo), cwd=self.root, env=self.env)
        self.assertIn("- Branch: `feat/x` (upstream: none) · ahead of main by 1, behind by 0 · 3 uncommitted files · last commit: ", out)
        self.assertIn("- Investigation location: `" + str(self.repo.resolve() / ".scratch") + "` (default)", out)
        for kind, template in TEMPLATES.items():
            self.assertRegex(out, rf"(?m)^- {re.escape(kind)}: `(?:docs|\.scratch)/n\d/{re.escape(template.name)}` · \d{{4}}-\d\d-\d\d", kind)
        self.assertNotIn("plain.md", out)
        self.assertIn("- Local tool record (", out)
        self.assertFalse((self.root / "state").exists(), "the scan must create nothing")

    def test_recorded_location_tickets_and_summary(self):
        (self.repo / "AGENTS.md").write_text("- **Investigations:** `docs/inv`\n")
        plan = self.repo / "docs/inv/order/plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("# Order\n\n**Readiness:** one slice blocked on the retry decision.\n\n## Delivery slices\n")
        (self.repo / ".scratch/order/issues").mkdir(parents=True)
        out = run(str(self.repo), cwd=self.root, env=self.env)
        self.assertIn("(recorded)", out)
        self.assertIn("- plan (plan-change): `docs/inv/order/plan.md` · ", out)
        self.assertIn(" · one slice blocked on the retry decision.", out)
        self.assertIn("- Local tickets (.scratch/order/issues): yes", out)

    def test_recorded_location_outside_the_checkout(self):
        (self.repo / "AGENTS.md").write_text("- Investigations: ../inv\n")
        plan = self.root / "inv/order/plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("# Order\n\n## Delivery slices\n")
        out = run(str(self.repo), cwd=self.root, env=self.env)
        self.assertIn(f"- plan (plan-change): `{plan.resolve()}` · ", out)

    def test_outside_git(self):
        plain = self.root / "plain"
        plain.mkdir()
        out = run(str(plain), cwd=self.root, env=self.env)
        self.assertIn("- Not a Git checkout", out)
        self.assertIn("- none found", out)
        self.assertFalse((plain / ".scratch").exists())


if __name__ == "__main__":
    unittest.main()

"""tool_setup_path.py --baseline/--compare reports project-file changes without storing untracked content."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/tool_setup_path.py"
SECRET = "FAKE_SECRET_FOR_BASELINE_TEST"


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {**os.environ, "XDG_STATE_HOME": str(self.root / "state")}
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.sh(self.repo, "git init -q && echo a > a && echo CLAUDE.md > .gitignore && git add . "
                           "&& git -c user.email=t@t -c user.name=t commit -qm init")

    def sh(self, cwd, script):
        subprocess.run(["bash", "-c", script], cwd=cwd, check=True, env=self.env)

    def tool(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def around(self, cwd, change):
        (cwd / "local-credentials.txt").write_text(SECRET + "\n")
        (cwd / "CLAUDE.md").write_text("c\n")
        self.assertEqual(self.tool("--baseline", str(cwd)), "baseline taken\n")
        self.sh(cwd, change)
        return self.tool("--compare", str(cwd))

    def assert_store_clean(self, cwd):
        objects = subprocess.run(["git", "cat-file", "--batch-all-objects", "--batch"], cwd=cwd,
                                 capture_output=True, check=True).stdout
        self.assertFalse(SECRET.encode() in objects, "untracked content reached the project's object store")
        self.assertFalse((self.root / "state").exists() and any((self.root / "state").rglob("baseline")),
                         "baseline left behind after --compare")

    def test_reports_changes_without_storing_untracked_content(self):
        out = self.around(self.repo, "echo x >> a; echo d >> CLAUDE.md; echo n > new.txt")
        self.assertIn("M\ta", out)
        self.assertIn("M\tCLAUDE.md", out)
        self.assertIn("A\tnew.txt", out)
        self.assertNotIn("index changed", out)
        self.assert_store_clean(self.repo)

    def test_unchanged(self):
        self.assertEqual(self.around(self.repo, "true"), "unchanged\n")

    def test_reports_index_change(self):
        out = self.around(self.repo, "echo x >> a; git add a")
        self.assertIn("index changed", out)
        self.assert_store_clean(self.repo)

    def test_linked_worktree(self):
        worktree = self.root / "wt"
        self.sh(self.repo, f"git worktree add -q '{worktree}'")
        self.assertIn("M\ta", self.around(worktree, "echo x >> a"))
        self.assert_store_clean(worktree)

    def test_outside_git(self):
        plain = self.root / "plain"
        plain.mkdir()
        (plain / "a").write_text("a\n")
        self.assertEqual(self.tool("--baseline", str(plain)), "baseline taken\n")
        (plain / "a").write_text("b\n")
        (plain / "n").write_text("n\n")
        self.assertEqual(self.tool("--compare", str(plain)), "M\ta\nA\tn\n")

    def test_show(self):
        self.assertTrue(self.tool("--show", str(self.repo)).startswith("none ("))


if __name__ == "__main__":
    unittest.main()

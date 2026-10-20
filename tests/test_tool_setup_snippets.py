"""The project-file baseline snippets in TOOL-SETUP.md run as documented."""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

DOC = (Path(__file__).resolve().parents[1] / "skills/TOOL-SETUP.md").read_text()
SECTION = DOC.split("## Preserve project files", 1)[1].split("\n## ", 1)[0]
GIT_BEFORE, GIT_AFTER, PLAIN_BEFORE = re.findall(r"```bash\n(.*?)```", SECTION, re.S)
PLAIN_AFTER = re.search(r"`(hashes \| diff [^`]+)`", SECTION).group(1)
SECRET = "FAKE_SECRET_FOR_SNAPSHOT_TEST"


def bash(cwd, script):
    return subprocess.run(["bash", "-c", script], cwd=cwd, capture_output=True, text=True, check=True).stdout


class GitBaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        bash(self.repo, "git init -q && echo a > a && echo CLAUDE.md > .gitignore && git add . "
                        "&& git -c user.email=t@t -c user.name=t commit -qm init")

    def run_baseline(self, cwd, change):
        (cwd / "local-credentials.txt").write_text(SECRET + "\n")
        (cwd / "CLAUDE.md").write_text("c\n")
        return bash(cwd, f"{GIT_BEFORE}\n{change}\n{GIT_AFTER}")

    def assert_store_clean(self, cwd, out):
        objects = subprocess.run(["git", "cat-file", "--batch-all-objects", "--batch"], cwd=cwd,
                                 capture_output=True, check=True).stdout
        self.assertFalse(SECRET.encode() in objects, "untracked content reached the project's object store")
        self.assertFalse(Path(re.search(r"objs=(\S+)", out).group(1)).exists())

    def test_reports_changes_without_storing_untracked_content(self):
        out = self.run_baseline(self.repo, "echo x >> a; echo d >> CLAUDE.md; echo n > new.txt")
        self.assertIn("M\ta", out)
        self.assertIn("M\tCLAUDE.md", out)
        self.assertIn("A\tnew.txt", out)
        self.assertNotIn("index changed", out)
        self.assert_store_clean(self.repo, out)

    def test_reports_index_change(self):
        out = self.run_baseline(self.repo, "echo x >> a; git add a")
        self.assertIn("index changed", out)
        self.assert_store_clean(self.repo, out)

    def test_linked_worktree(self):
        worktree = Path(self.tmp.name) / "wt"
        bash(self.repo, f"git worktree add -q '{worktree}'")
        out = self.run_baseline(worktree, "echo x >> a")
        self.assertIn("M\ta", out)
        self.assert_store_clean(worktree, out)


class PlainBaselineTests(unittest.TestCase):
    def test_reports_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a").write_text("a\n")
            out = bash(tmp, f"{PLAIN_BEFORE}\necho x >> a\n{PLAIN_AFTER}")
            self.assertRegex(out, r"[<>] \w+\s+\./a")


if __name__ == "__main__":
    unittest.main()

"""investigation_dir.py honours a recorded location and keeps `.scratch/` out of commits."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/investigation_dir.py"


def run(*args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


class InvestigationDirTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

    def test_default_is_excluded_scratch(self):
        path = run("PR 12: bulk/discount", cwd=self.repo / ".")
        self.assertEqual(Path(path), self.repo.resolve() / ".scratch/PR-12-bulk-discount")
        self.assertTrue(Path(path).is_dir())
        run("again", cwd=self.repo)
        (Path(path) / "note.md").write_text("n\n")
        status = subprocess.run(["git", "status", "--porcelain", "--ignored"], cwd=self.repo, capture_output=True, text=True).stdout
        self.assertIn("!! .scratch/", status)
        self.assertEqual((self.repo / ".git/info/exclude").read_text().count("/.scratch/"), 1)

    def test_recorded_location(self):
        (self.repo / "AGENTS.md").write_text("# Notes\n\n- Investigations: `docs/investigations`\n")
        path = run("bug", str(self.repo), cwd=self.tmp.name)
        self.assertEqual(Path(path), self.repo.resolve() / "docs/investigations/bug")
        self.assertFalse((self.repo / ".scratch").exists())

    def test_outside_git(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        self.assertEqual(Path(run("x", cwd=plain)), plain.resolve() / ".scratch/x")


if __name__ == "__main__":
    unittest.main()

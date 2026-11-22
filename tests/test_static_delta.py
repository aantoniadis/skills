import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "evals" / "real-pr" / "static_delta.py"
# A stand-in checker: one diagnostic for each line of a.py that contains "bad" or "note".
CHECKER = ("import pathlib\n"
           "for n, line in enumerate(pathlib.Path('a.py').read_text().splitlines(), 1):\n"
           "    if 'bad' in line or 'note' in line: print(f'a.py:{n}: error: {line.strip()}')\n")


class StaticDeltaTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.git("init", "-q", "-b", "main")
        self.commit("x = 1  # note\n")

    def git(self, *args):
        subprocess.run(["git", "-C", self.dir.name, "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       check=True, capture_output=True)

    def commit(self, text):
        Path(self.dir.name, "a.py").write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", "change")

    def run_delta(self, base="HEAD~1", head="HEAD"):
        return subprocess.run([sys.executable, str(SCRIPT), "--base", base, "--head", head, "--repo", self.dir.name,
                               "--", sys.executable, "-c", CHECKER], capture_output=True, text=True)

    def test_moved_diagnostic_is_not_new(self):
        self.commit("\n\nx = 1  # note\n")
        result = self.run_delta()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_new_diagnostic_is_listed(self):
        self.commit("\nx = 1  # note\ny = bad\n")
        result = self.run_delta()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("a.py:3: error: y = bad", result.stdout)
        self.assertNotIn("note", result.stdout)

    def test_unknown_revision_exits_2(self):
        self.assertEqual(self.run_delta(base="no-such-rev").returncode, 2)


if __name__ == "__main__":
    unittest.main()

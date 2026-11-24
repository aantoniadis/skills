import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "find-bugs" / "scripts"
TABLE = """# Candidates

| Candidate | Finders | Disposition |
|---|---|---|
| release blocks | 1, 3 | delivered |
| release(force) blocks | 2 | merged into release blocks |
| bad path waits | 2 | delivered |
| pickle breaks | 1 | delivered |
| hostname space | 4 | delivered |
| docs stale | 1, 2 | delivered |
| lifetime text | 3 | dropped: same at base: base prints the same text, probe p3 |
"""


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, cwd=cwd)


class RemainingTest(unittest.TestCase):
    def table(self, text):
        handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        handle.write(text)
        handle.close()
        self.addCleanup(Path(handle.name).unlink)
        return handle.name

    def test_estimate_counts_delivered_rows_only(self):
        result = run("remaining.py", "--finders", "4", self.table(TABLE))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("7 candidates: 5 delivered, 2 merged or dropped.", result.stdout)
        self.assertIn("found by one finder: 3; by two: 2.", result.stdout)
        # Chao2, bias-corrected: 5 + (3/4) * 3 * 2 / (2 * 3) = 5.75.
        self.assertIn("about 6; this search found about 87%", result.stdout)

    def test_row_without_disposition_fails(self):
        result = run("remaining.py", "--finders", "4", self.table(TABLE.replace("| 4 | delivered |", "| 4 | maybe |")))
        self.assertEqual(result.returncode, 1)
        self.assertIn("- hostname space", result.stdout)

    def test_drop_needs_counterevidence(self):
        result = run("remaining.py", "--finders", "4", self.table(TABLE.replace("dropped: same at base: base prints", "dropped: same at base:")
                                                                  .replace(" the same text, probe p3", "")))
        self.assertEqual(result.returncode, 1)
        self.assertIn("- lifetime text", result.stdout)

    def test_drop_needs_an_allowed_ground(self):
        for reason in ("minor, efficiency only", "base prints the same text", "never compared"):
            result = run("remaining.py", self.table(TABLE.replace("same at base: base prints the same text, probe p3", reason)))
            self.assertEqual(result.returncode, 1, reason)
            self.assertIn("- lifetime text", result.stdout)
            self.assertIn("A drop names its ground", result.stdout)
        for ground in ("absent at head", "same at base", "documented intent", "Same At Base"):
            result = run("remaining.py", self.table(TABLE.replace("same at base: base prints", f"{ground}: base prints")))
            self.assertEqual(result.returncode, 0, ground)

    def test_without_finders_checks_dispositions_only(self):
        result = run("remaining.py", self.table(TABLE))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "7 candidates: 5 delivered, 2 merged or dropped.\n")
        result = run("remaining.py", self.table(TABLE.replace("| 4 | delivered |", "| 4 | maybe |")))
        self.assertEqual(result.returncode, 1)

    def test_missing_columns_exit_2(self):
        self.assertEqual(run("remaining.py", "--finders", "4", self.table("| a | b |\n|---|---|\n| x | y |\n")).returncode, 2)


class FailurePointsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.git("init", "-q", "-b", "main")
        self.commit({"lock.py": "def take():\n    return 1\n"})

    def git(self, *args):
        subprocess.run(["git", "-C", self.dir.name, "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       check=True, capture_output=True)

    def commit(self, files):
        for name, text in files.items():
            Path(self.dir.name, name).write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", "change")

    def test_lists_added_calls_that_can_fail(self):
        self.commit({"lock.py": "import os\n\ndef take(path):\n    fd = os.open(path, os.O_CREAT)\n"
                                "    # os.unlink(path) in a comment\n    total = 1 + 2\n    os.close(fd)\n",
                     "test_lock.py": "import os\nos.unlink('x')\n"})
        result = run("failure_points.py", "--base", "HEAD~1", "--head", "HEAD", "--repo", self.dir.name)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("`lock.py:4` in `take`", result.stdout)
        self.assertIn("`lock.py:7`", result.stdout)
        self.assertNotIn("comment", result.stdout)
        self.assertNotIn("total", result.stdout)
        self.assertNotIn("test_lock.py", result.stdout)

    def test_unknown_revision_exits_2(self):
        result = run("failure_points.py", "--base", "nope", "--head", "HEAD", "--repo", self.dir.name)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()

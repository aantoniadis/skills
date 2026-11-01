"""weakened_checks.py lists suppressions, skipped tests, removed tests and assertions, stubs, and threshold edits."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/find-bugs/scripts/weakened_checks.py"


class WeakenedChecksTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "app.py").write_text("def total(items):\n    return sum(items)\n")
        (self.repo / "test_app.py").write_text("def test_total():\n    assert total([1]) == 1\n\ndef test_empty():\n    assert total([]) == 0\n")
        (self.repo / "jest.config.js").write_text("module.exports = { coverageThreshold: { global: { lines: 80 } } };\n")
        self.base = self.commit()

    def git(self, *args):
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        return subprocess.check_output(["git", "-C", str(self.repo), *args], env=env, text=True).strip()

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "fixture")
        return self.git("rev-parse", "HEAD")

    def run_script(self, base, head):
        result = subprocess.run([sys.executable, str(SCRIPT), "--base", base, "--head", head, "--repo", str(self.repo)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_each_lead_class_is_reported_with_its_line(self):
        (self.repo / "app.py").write_text("def total(items):  # type: ignore\n    raise NotImplementedError\n")
        (self.repo / "test_app.py").write_text("import pytest\n\n@pytest.mark.skip\ndef test_total():\n    total([1])\n")
        (self.repo / "jest.config.js").write_text("module.exports = { coverageThreshold: { global: { lines: 60 } } };\n")
        out = self.run_script(self.base, self.commit())
        self.assertIn("## suppression\n- `app.py:1` `+def total(items):  # type: ignore`", out)
        self.assertIn("## stub\n- `app.py:2` `+raise NotImplementedError`", out)
        self.assertIn("## skipped or focused test\n- `test_app.py:3` `+@pytest.mark.skip`", out)
        self.assertIn("## removed test\n", out)
        self.assertIn("- `test_app.py:4` `-def test_empty():`", out)
        self.assertIn("## removed assertion\n", out)
        self.assertIn("- `test_app.py:2` `-assert total([1]) == 1`", out)
        self.assertIn("## threshold or coverage configuration changed\n", out)
        self.assertIn("`-module.exports = { coverageThreshold: { global: { lines: 80 } } };`", out)
        self.assertIn("`+module.exports = { coverageThreshold: { global: { lines: 60 } } };`", out)

    def test_deleted_test_file_is_reported(self):
        (self.repo / "test_app.py").unlink()
        (self.repo / "app.py").write_text("-- not a header\ndef total(items):\n    return sum(items)\n")
        out = self.run_script(self.base, self.commit())
        self.assertIn("- `test_app.py:1` `-def test_total():`", out)
        self.assertIn("- `test_app.py:2` `-assert total([1]) == 1`", out)

    def test_clean_change_reports_none(self):
        (self.repo / "app.py").write_text("def total(items):\n    return sum(items) + 0\n")
        self.assertEqual(self.run_script(self.base, self.commit()).strip(),
                         "No weakened checks found between the two commits by these patterns.")

    def test_bad_ref_exits_2(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--base", "nope", "--head", "HEAD", "--repo", str(self.repo)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()

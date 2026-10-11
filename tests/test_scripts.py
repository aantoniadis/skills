"""Run the script-style checks under unittest, so `unittest discover` covers them too."""

from pathlib import Path
import subprocess
import sys
import unittest


TESTS = Path(__file__).resolve().parent


class ScriptChecks(unittest.TestCase):
    def test_scripts_pass(self):
        for name in ("test_skill_namespace.py",):
            with self.subTest(script=name):
                result = subprocess.run([sys.executable, str(TESTS / name)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()

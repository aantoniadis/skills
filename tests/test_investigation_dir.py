"""investigation_dir.py honours a recorded location and keeps `.scratch/` out of commits. Inside herdr-core
it also labels its session with the location."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/investigation_dir.py"


# The suite can run inside herdr-core; without this, every test would label the real session.
OUTSIDE = {k: v for k, v in os.environ.items() if not k.startswith("HC_")}


def run(*args, cwd, env=OUTSIDE):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, check=True, env=env).stdout.strip()


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

    def herdr_core(self, body):
        """A stub `hc` first on PATH whose shell body runs for every call, and the session id of this session."""
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "hc").write_text(f"#!/bin/sh\n{body}\n")
        (bin_dir / "hc").chmod(0o755)
        return {**OUTSIDE, "PATH": f"{bin_dir}{os.pathsep}{OUTSIDE['PATH']}", "HC_TERMINAL_ID": "t7"}

    def test_labels_the_session_inside_herdr_core(self):
        log = Path(self.tmp.name) / "hc.log"
        path = run("order export", cwd=self.repo, env=self.herdr_core(f'echo "$@" >> {log}'))
        self.assertEqual(Path(path), self.repo.resolve() / ".scratch/order-export", "stdout stays the location alone")
        self.assertEqual(log.read_text(), "label t7 notes=.scratch/order-export\n")
        run("order export", cwd=self.repo)
        self.assertEqual(log.read_text().count("\n"), 1, "no call outside herdr-core")

    def test_a_failing_hc_does_not_fail_the_location(self):
        path = run("bug", cwd=self.repo, env=self.herdr_core("echo 'core is not running' >&2; exit 1"))
        self.assertEqual(Path(path), self.repo.resolve() / ".scratch/bug")

    def test_recorded_location(self):
        (self.repo / "AGENTS.md").write_text("# Notes\n\n- Investigations: `docs/investigations`\n")
        path = run("bug", str(self.repo), cwd=self.tmp.name)
        self.assertEqual(Path(path), self.repo.resolve() / "docs/investigations/bug")
        self.assertFalse((self.repo / ".scratch").exists())

    def test_recorded_location_bold_and_spaced(self):
        for line, expected in (("- **Investigations:** `docs/inv`", "docs/inv"),
                               ("**Investigations:** docs/inv", "docs/inv"),
                               ("- Investigations: `docs/my notes`", "docs/my notes")):
            (self.repo / "AGENTS.md").write_text(f"# Notes\n\n{line}\n")
            self.assertEqual(Path(run("bug", str(self.repo), cwd=self.tmp.name)), self.repo.resolve() / expected / "bug", line)

    def test_outside_git(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        self.assertEqual(Path(run("x", cwd=plain)), plain.resolve() / ".scratch/x")


if __name__ == "__main__":
    unittest.main()

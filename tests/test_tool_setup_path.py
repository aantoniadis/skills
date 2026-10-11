"""Local tool state stays outside source trees and is discoverable from subdirectories."""

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "skills/tool_setup_path.py"
spec = importlib.util.spec_from_file_location("tool_setup_path", MODULE)
setup_path = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_path)


class ToolSetupPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "project with spaces "
        self.repo.mkdir()
        self.state = self.root / "state"
        self.env = patch.dict(os.environ, {"XDG_STATE_HOME": str(self.state)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def test_git_root_subdirectory_and_symlink_share_record_without_writes(self):
        self.git("init", "-q")
        for name in ("AGENTS.md", "CLAUDE.md", "package-lock.json"):
            (self.repo / name).write_text("existing project content\n")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "project files")
        (self.repo / "AGENTS.md").write_text("user's uncommitted changes\n")
        status = self.git("status", "--porcelain", "--untracked-files=all")
        child = self.repo / "src"
        child.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        before = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*"))
        record = setup_path.record_path(self.repo)
        self.assertEqual(record, setup_path.record_path(child))
        self.assertEqual(record, setup_path.record_path(alias))
        self.assertFalse(self.state.exists())
        self.assertEqual(before, sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*")))
        record.parent.mkdir(parents=True)
        record.write_text("Local test command: python3 -m unittest\n")
        lookup = subprocess.check_output(
            ["python3", str(MODULE), str(child)], text=True, cwd=alias,
        )
        self.assertEqual(Path(lookup.removesuffix("\n")).read_text(), record.read_text())
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all"), status)
        self.assertEqual((self.repo / "AGENTS.md").read_text(), "user's uncommitted changes\n")
        self.assertEqual((self.repo / "CLAUDE.md").read_text(), "existing project content\n")
        self.assertEqual((self.repo / "package-lock.json").read_text(), "existing project content\n")

    def test_worktrees_have_independent_records(self):
        self.git("init", "-q")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "--allow-empty", "-qm", "initial")
        worktree = self.root / "worktree"
        self.git("worktree", "add", "--detach", str(worktree))
        self.assertNotEqual(setup_path.record_path(self.repo), setup_path.record_path(worktree))

    def test_non_git_projects(self):
        other = self.root / "other"
        other.mkdir()
        expected = setup_path.record_path(self.repo)
        self.assertNotEqual(expected, setup_path.record_path(other))

    def test_missing_git_is_reported(self):
        with patch.object(setup_path.subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(ValueError, "Git is unavailable"):
                setup_path.record_path(self.repo)

    def test_inherited_git_overrides_do_not_change_project_or_index(self):
        self.git("init", "-q")
        child = self.repo / "src"
        child.mkdir()
        expected = setup_path.record_path(self.repo)
        other = self.root / "other"
        other.mkdir()
        subprocess.check_call(["git", "-C", str(other), "init", "-q"])
        for overrides in (
            {"GIT_WORK_TREE": str(other)},
            {"GIT_DIR": str(self.root / "missing")},
            {"GIT_COMMON_DIR": str(other / ".git")},
            {"GIT_CEILING_DIRECTORIES": str(self.repo)},
            {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.worktree", "GIT_CONFIG_VALUE_0": str(other)},
        ):
            with self.subTest(overrides=overrides), patch.dict(os.environ, overrides):
                self.assertEqual(expected, setup_path.record_path(child))

    def test_broken_repository_is_not_treated_as_non_git(self):
        (self.repo / ".git").write_text("gitdir: /nonexistent/setup-tools-test\n")
        with self.assertRaisesRegex(ValueError, "Git discovery failed"):
            setup_path.record_path(self.repo)

    def test_git_errors_are_reported(self):
        failure = subprocess.CompletedProcess([], 128, "", "fatal: dubious ownership")
        with patch.object(setup_path.subprocess, "run", return_value=failure):
            with self.assertRaisesRegex(ValueError, "dubious ownership"):
                setup_path.record_path(self.repo)

    def test_tracked_record_in_another_repository_is_readable_but_not_writable(self):
        record = setup_path.record_path(self.repo)
        record.parent.mkdir(parents=True)
        subprocess.check_call(["git", "-C", str(self.state), "init", "-q"])
        record.write_text("preserve tracked state\n")
        subprocess.check_call(["git", "-C", str(self.state), "add", "."])
        with patch.dict(os.environ, {"GIT_INDEX_FILE": str(self.root / "empty-index")}):
            self.assertEqual(record, setup_path.record_path(self.repo))
            with self.assertRaisesRegex(ValueError, "tracked"):
                setup_path.record_path(self.repo, for_write=True)
        self.assertEqual(record.read_text(), "preserve tracked state\n")

    def test_symlink_to_tracked_file_is_not_writable(self):
        record = setup_path.record_path(self.repo)
        record.parent.mkdir(parents=True)
        other = self.root / "other"
        other.mkdir()
        subprocess.check_call(["git", "-C", str(other), "init", "-q"])
        victim = other / "notes.md"
        victim.write_text("user content\n")
        subprocess.check_call(["git", "-C", str(other), "add", "."])
        record.symlink_to(victim)
        self.assertEqual(victim, setup_path.record_path(self.repo))
        with self.assertRaisesRegex(ValueError, "tracked"):
            setup_path.record_path(self.repo, for_write=True)
        self.assertEqual(victim.read_text(), "user content\n")

    def test_symlink_to_untracked_project_instructions_is_not_writable(self):
        record = setup_path.record_path(self.repo)
        record.parent.mkdir(parents=True)
        for name in ("CLAUDE.md", "AGENTS.md", "AGENT.md"):
            with self.subTest(name=name):
                victim = self.root / name
                victim.write_text("user instructions\n")
                record.symlink_to(victim)
                with self.assertRaisesRegex(ValueError, "project instructions"):
                    setup_path.record_path(self.repo, for_write=True)
                self.assertEqual(victim.read_text(), "user instructions\n")
                record.unlink()

    def test_corrupt_destination_index_is_not_treated_as_untracked(self):
        self.state.mkdir()
        subprocess.check_call(["git", "-C", str(self.state), "init", "-q"])
        (self.state / ".git/index").write_bytes(b"broken index")
        with self.assertRaisesRegex(ValueError, "Git tracking check failed"):
            setup_path.record_path(self.repo, for_write=True)

    def test_record_directory_is_rejected_for_writing(self):
        record = setup_path.record_path(self.repo)
        record.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "must be a file"):
            setup_path.record_path(self.repo, for_write=True)

    def test_untracked_state_in_another_repository_is_writable(self):
        self.state.mkdir()
        subprocess.check_call(["git", "-C", str(self.state), "init", "-q"])
        record = setup_path.record_path(self.repo, for_write=True)
        self.assertFalse(record.parent.exists())
        record.parent.mkdir(parents=True)
        record.write_text("retained operation\n")
        self.assertEqual(record, setup_path.record_path(self.repo, for_write=True))

    def test_write_check_cli_creates_nothing(self):
        result = subprocess.run(
            ["python3", str(MODULE), "--for-write", str(self.repo)], text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.rstrip("\n")), setup_path.record_path(self.repo))
        self.assertFalse(self.state.exists())

    def test_relative_state_home_uses_standard_default(self):
        with patch.dict(os.environ, {"XDG_STATE_HOME": "relative"}), patch.object(Path, "home", return_value=self.root / "home"):
            record = setup_path.record_path(self.repo)
        self.assertTrue(record.is_relative_to(self.root / "home/.local/state"))

    def test_state_inside_project_is_rejected_including_symlinks(self):
        self.git("init", "-q")
        child = self.repo / "state"
        child.mkdir()
        self.state.symlink_to(child, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "outside the project"):
            setup_path.record_path(self.repo)

    def test_cli_reports_invalid_project_without_creating_it(self):
        missing = self.root / "missing"
        result = subprocess.run(["python3", str(MODULE), str(missing)], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr)
        self.assertFalse(missing.exists())
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()

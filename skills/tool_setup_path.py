#!/usr/bin/env python3
"""Print the local tool record path for a project, show the record, or take and
compare the project-file baseline that setup keeps outside the project."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

INSTRUCTIONS = ("CLAUDE.md", "AGENTS.md", "AGENT.md")


def git(directory, *args, extra_env=None, literal=True):
    # Inspect this path, independently of the invoking Git process's overrides.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["LC_ALL"] = "C"
    env.update(extra_env or {})
    try:
        return subprocess.run(
            ["git", *(["--literal-pathspecs"] if literal else []), "-C", str(directory), *args],
            capture_output=True, text=True, check=False, env=env,
        )
    except FileNotFoundError as error:
        raise ValueError("Git is unavailable; cannot safely resolve local tool state") from error


def git_root(directory):
    result = git(directory, "rev-parse", "--show-toplevel")
    if result.returncode == 0:
        return Path(result.stdout.removesuffix("\n")).resolve()
    markers = (parent / ".git" for parent in (directory, *directory.parents))
    has_marker = any(
        marker.is_symlink() or marker.is_file() or (marker.is_dir() and any(marker.iterdir()))
        for marker in markers
    )
    if not has_marker and result.returncode == 128 and result.stderr.startswith((
        "fatal: not a git repository (or any of the parent directories):",
        "fatal: not a git repository (or any parent up to mount point ",
    )):
        return None
    raise ValueError(f"Git discovery failed at {directory}: {result.stderr.strip()}")


def check_write_path(path):
    if path.name in INSTRUCTIONS:
        raise ValueError(f"tool state cannot overwrite project instructions: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"tool record must be a file: {path}")
    directory = path.parent
    while not directory.exists():
        directory = directory.parent
    root = git_root(directory)
    if root is not None:
        result = git(root, "ls-files", "--error-unmatch", "--", str(path.relative_to(root)))
        if result.returncode == 0:
            raise ValueError(f"tool state cannot overwrite a Git-tracked file: {path}")
        if result.returncode != 1:
            raise ValueError(f"Git tracking check failed at {path}: {result.stderr.strip()}")


def record_path(project, *, for_write=False):
    root = Path(project).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("project must be a directory")
    root = git_root(root) or root

    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    if not state.is_absolute():
        state = Path.home() / ".local/state"
    key = hashlib.sha256(os.fsencode(root)).hexdigest()
    path = (state / "aantoniadis-skills/projects" / key / "tools.md").resolve()
    if path.is_relative_to(root):
        raise ValueError("tool state must be outside the project; set XDG_STATE_HOME to an external directory")
    if for_write:
        check_write_path(path)
    return path


def checked(result):
    if result.returncode != 0:
        raise ValueError(f"git {' '.join(result.args[result.args.index('-C') + 2:])} failed: {result.stderr.strip()}")
    return result.stdout


def snapshot(root, objects):
    # Untracked content goes to `objects`, never the project's object store.
    alternate = (root / checked(git(root, "rev-parse", "--git-path", "objects")).strip()).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": f"{tmp}/index", "GIT_OBJECT_DIRECTORY": str(objects),
               "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(alternate)}
        checked(git(root, "add", "-A", ".", extra_env=env))
        ignored = checked(git(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", *INSTRUCTIONS, extra_env=env))
        names = [name for name in ignored.split("\0") if name]
        if names:
            checked(git(root, "add", "--force", "--", *names, extra_env=env))
        tree = checked(git(root, "write-tree", extra_env=env)).strip()
    index = hashlib.sha256(checked(git(root, "ls-files", "--stage")).encode()).hexdigest()
    return tree, index, env


def file_hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink()}


def baseline(project):
    root = Path(project).expanduser().resolve(strict=True)
    root = git_root(root) or root
    state = record_path(root).parent / "baseline"
    shutil.rmtree(state, ignore_errors=True)
    (state / "objects").mkdir(parents=True)
    if git_root(root) is None:
        record = {"files": file_hashes(root)}
    else:
        tree, index, _ = snapshot(root, state / "objects")
        record = {"tree": tree, "index": index}
    (state / "baseline.json").write_text(json.dumps(record))
    return "baseline taken"


def compare(project):
    root = Path(project).expanduser().resolve(strict=True)
    root = git_root(root) or root
    state = record_path(root).parent / "baseline"
    try:
        record = json.loads((state / "baseline.json").read_text())
    except FileNotFoundError:
        raise ValueError("no baseline: run --baseline first") from None
    try:
        if "files" in record:
            before, after = record["files"], file_hashes(root)
            changes = [f"{'D' if name not in after else 'A' if name not in before else 'M'}\t{name}"
                       for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]
        else:
            tree, index, env = snapshot(root, state / "objects")
            changes = checked(git(root, "diff-tree", "-r", "--name-status", record["tree"], tree, extra_env=env)).splitlines()
            if index != record["index"]:
                changes.append("index changed")
    finally:
        shutil.rmtree(state, ignore_errors=True)
    return "\n".join(changes) or "unchanged"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".", help="project directory (default: current directory)")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--for-write", action="store_true", help="also reject tracked files and project instructions at the destination")
    action.add_argument("--show", action="store_true", help="print the record, or 'none' when it does not exist")
    action.add_argument("--baseline", action="store_true", help="record the project files before commands that can write")
    action.add_argument("--compare", action="store_true", help="list project files changed since --baseline, then delete the baseline")
    args = parser.parse_args()
    try:
        if args.show:
            path = record_path(args.project)
            print(path.read_text() if path.is_file() else f"none ({path})")
        elif args.baseline:
            print(baseline(args.project))
        elif args.compare:
            print(compare(args.project))
        else:
            print(record_path(args.project, for_write=args.for_write))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")

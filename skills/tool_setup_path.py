#!/usr/bin/env python3
"""Print the local tool record path for a project without creating files."""

import argparse
import hashlib
import os
import subprocess
from pathlib import Path


def git(directory, *args):
    # Inspect this path, independently of the invoking Git process's overrides.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["LC_ALL"] = "C"
    try:
        return subprocess.run(
            ["git", "--literal-pathspecs", "-C", str(directory), *args],
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
    if path.name in {"AGENTS.md", "AGENT.md", "CLAUDE.md"}:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".", help="project directory (default: current directory)")
    parser.add_argument("--for-write", action="store_true", help="also reject tracked files and project instructions at the destination")
    args = parser.parse_args()
    try:
        print(record_path(args.project, for_write=args.for_write))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")

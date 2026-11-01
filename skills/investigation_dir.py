#!/usr/bin/env python3
"""Create and print the investigation location for a topic, keeping `.scratch/` out of commits."""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tool_setup_path import INSTRUCTIONS, checked, git, git_root, project_root  # noqa: E402

# `- Investigations: docs/inv` or `- **Investigations:** `docs/my notes``; a path with spaces needs backticks.
RECORD = re.compile(r"^[\s*-]*Investigations:\**[ \t]*(?:`([^`\n]+)`|(\S+))", re.M)


def investigation_dir(project, topic):
    slug = re.sub(r"[^\w.-]+", "-", topic).strip("-.") or "investigation"
    root = project_root(project)
    repo = git_root(root)
    for name in INSTRUCTIONS:
        match = RECORD.search((root / name).read_text(errors="replace")) if (root / name).is_file() else None
        if match:
            base = (root / (match.group(1) or match.group(2))).resolve()
            break
    else:
        base = root / ".scratch"
        # Exit 1 means not ignored; any other exit is a Git error, not a reason to edit the exclude file.
        ignored = git(root, "check-ignore", "-q", ".scratch/x", literal=False).returncode if repo else 0
        if ignored not in (0, 1):
            raise ValueError(f"git check-ignore failed at {root}")
        if ignored == 1:
            exclude = root / checked(git(root, "rev-parse", "--git-path", "info/exclude")).strip()
            exclude.parent.mkdir(parents=True, exist_ok=True)
            text = exclude.read_text() if exclude.is_file() else ""
            exclude.write_text(text + ("" if text.endswith("\n") or not text else "\n") + "/.scratch/\n")
    path = base / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", help="short name for the work, such as the PR or bug")
    parser.add_argument("project", nargs="?", default=".", help="project directory (default: current directory)")
    args = parser.parse_args()
    try:
        print(investigation_dir(args.project, args.topic))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")

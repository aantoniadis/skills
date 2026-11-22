#!/usr/bin/env python3
"""List the diagnostics a type checker or linter reports at the head and not at the base.

Leads, not verdicts. The command runs in an exported copy of each commit, and the
two outputs are compared with file positions removed, so a diagnostic that only
moved is not a difference. Give the checker the package and the code that uses it,
such as tests and documented examples: a package can check clean while a consumer
of its changed types no longer does.

  static_delta.py --base <base> --head <head> [--repo <checkout>] [--link <path>]... -- <checker> [args...]

Write a path inside the command relative to the repository root. A copy holds only
committed files: --link names a path in the checkout that the checker needs beyond
them, such as node_modules, and links it into each copy. The last line gives each
copy's exit status; when both copies fail with the same text, the checker did not
run there. Exit 0 with no new diagnostic, 1 with at least one, 2 for invalid inputs
or failed Git operations. The checkout is not touched and the copies are removed.
"""
import argparse
from collections import Counter
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile


def export(repo, rev, target):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", rev], env=env, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip() or f"git failed with exit {result.returncode}")
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        archive.extractall(target, filter="data")


def diagnostics(command, root):
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    return result.returncode, [line.replace(str(root) + os.sep, "").replace(str(root), ".").rstrip()
                               for line in (result.stdout + result.stderr).splitlines()]


def key(line):
    # shortcut: every digit run is dropped before comparing, so two diagnostics that differ only
    # in a number compare equal; compare the checker's structured output when that matters.
    return re.sub(r"\d+", "", line).strip()


def new_at_head(base, head):
    seen, found = Counter(key(line) for line in base), []
    for line in head:
        if not re.search(r"\w", key(line)):  # gutters and underlines carry no diagnostic
            continue
        if seen[key(line)]:
            seen[key(line)] -= 1
        else:
            found.append(line)
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--link", action="append", default=[], metavar="PATH",
                        help="a path in the checkout to link into each copy, such as node_modules")
    parser.add_argument("command", nargs="+", help="the checker command, after --")
    args = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="static-delta-") as scratch:
            statuses, outputs = [], []
            for name, rev in (("base", args.base), ("head", args.head)):
                root = Path(scratch) / name
                root.mkdir()
                export(args.repo, rev, root)
                for linked in args.link:
                    source = (Path(args.repo) / linked).resolve(strict=True)
                    (root / linked).parent.mkdir(parents=True, exist_ok=True)
                    (root / linked).symlink_to(source, target_is_directory=source.is_dir())
                status, lines = diagnostics(args.command, root)
                statuses.append(status)
                outputs.append(lines)
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(2, f"{error}\n")
    found = new_at_head(*outputs)
    if found:
        print(f"{len(found)} output lines at the head that the base lacks:")
        print("\n".join(found))
    else:
        print("No diagnostic at the head that the base lacks.")
    print(f"Checker exit status: base {statuses[0]}, head {statuses[1]}.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

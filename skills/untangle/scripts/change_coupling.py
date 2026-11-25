#!/usr/bin/env python3
"""List the files that change most, and the pairs of files that change in the same commits.

Leads, not findings: a pair that changes together with no dependency between its files often
holds one rule in two places, and a file that changes often is where a rework pays back. Squash
merges, bulk commits, renames, and a short history all distort the counts, so read both files
of a pair before recording anything. Run from the repository root, or pass --repo. Exit 2 for
invalid inputs or failed Git operations. No files are written.
"""
import argparse
from collections import Counter
from itertools import combinations
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys

NOISE = re.compile(r"(^|/)(node_modules|vendor|dist|build|target|\.venv|__pycache__)/|\.lock$|(^|/)package-lock\.json$"
                   r"|(^|/)(pnpm-lock|yarn)\.\w+$|\.min\.(js|css)$|\.(png|jpe?g|gif|svg|ico|pdf|woff2?|snap)$")


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def commits(log):
    """The file list of each commit in `git log --format=@%H --name-only` output."""
    current = None
    for line in log.splitlines():
        if line.startswith("@"):
            if current:
                yield current
            current = []
        elif line.strip() and current is not None:
            current.append(line.strip())
    if current:
        yield current


def analyze(changes, keep, max_files=30):
    """Change counts per file and shared-commit counts per pair, over the files `keep` accepts.
    A commit that touches more than max_files kept files is a bulk change: it counts for no pair."""
    revisions, shared, bulk = Counter(), Counter(), 0
    for files in changes:
        files = sorted({path for path in files if keep(path)})
        revisions.update(files)
        if len(files) > max_files:
            bulk += 1
            continue
        shared.update(combinations(files, 2))
    return revisions, shared, bulk


def pairs(revisions, shared, min_shared=3):
    """(shared commits, degree, a, b), strongest first. Degree is the share of the pair's average
    revisions that touched both files, in percent."""
    rows = [(count, round(200 * count / (revisions[a] + revisions[b])), a, b)
            for (a, b), count in shared.items() if count >= min_shared]
    return sorted(rows, key=lambda row: (-row[0], -row[1], row[2], row[3]))


def read_edges(path):
    """Dependency edges as unordered pairs, from a TSV of `from<TAB>to` repository paths."""
    edges = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and not line.startswith("#"):
                edges.add(frozenset(parts[:2]))
    return edges


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="limit the history to these paths; default is the whole repository")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--since", default="12 months ago", help="history window; default: 12 months ago")
    parser.add_argument("--max-files", type=int, default=30, help="a commit touching more files counts for no pair")
    parser.add_argument("--min-shared", type=int, default=3, help="shared commits a pair needs to be listed")
    parser.add_argument("--top", type=int, default=30, help="rows per table")
    parser.add_argument("--edges", help="TSV of dependency edges (import_edges.py writes one); marks pairs with no dependency")
    parser.add_argument("--exclude", action="append", default=[], help="regular expression for paths to leave out; repeatable")
    args = parser.parse_args()
    try:
        exclude = [re.compile(pattern) for pattern in args.exclude]
        shallow = git(args.repo, "rev-parse", "--is-shallow-repository").strip() == "true"
        tracked = set(git(args.repo, "ls-files", "--", *args.paths).splitlines())
        log = git(args.repo, "log", f"--since={args.since}", "--no-merges", "--format=@%H", "--name-only", "--", *args.paths)
        edges = read_edges(args.edges) if args.edges else None
    except (ValueError, OSError, re.error) as error:
        print(f"change_coupling: {error}", file=sys.stderr)
        return 2
    # A file that no longer exists cannot be reworked; its history stays out of the tables.
    keep = lambda path: path in tracked and not NOISE.search(path) and not any(p.search(path) for p in exclude)
    changes = list(commits(log))
    revisions, shared, bulk = analyze(changes, keep, args.max_files)
    print(f"History: {len(changes)} commits since {args.since}; {bulk} bulk commits (more than {args.max_files} files) count for no pair.")
    if shallow:
        print("WARNING: this clone is shallow, so the counts cover only the fetched commits. "
              "Deepen it (git fetch --depth=<n>) or state the limit beside every count.")
    if not revisions:
        print("No changed files in this window and scope.")
        return 0
    print(f"\nMost changed files (top {args.top}):\n\nchanges\tfile")
    for path, count in revisions.most_common(args.top):
        print(f"{count}\t{path}")
    rows = pairs(revisions, shared, args.min_shared)
    print(f"\nFiles that change together ({len(rows)} pairs with at least {args.min_shared} shared commits; top {args.top}):\n")
    print("shared\tdegree\tdirectories\tdependency\tpair")
    for count, degree, a, b in rows[:args.top]:
        across = "different" if PurePosixPath(a).parent != PurePosixPath(b).parent else "same"
        linked = "not given" if edges is None else ("yes" if frozenset((a, b)) in edges else "none found")
        print(f"{count}\t{degree}%\t{across}\t{linked}\t{a}  <->  {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

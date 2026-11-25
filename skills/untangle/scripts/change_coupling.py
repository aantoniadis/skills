#!/usr/bin/env python3
"""List the files that change most, and the pairs of files that change in the same commits.

Leads, not findings: a pair that changes together with no dependency between its files often
holds one rule in two places, and a file that changes often is where a rework pays back. With
paths given, the pairs still include partners outside them, marked as such: the other half of
a rule often lives outside the component. Squash merges, bulk commits, renames, and a short
history all distort the counts, so read both files of a pair before recording anything. Run from the repository root, or pass --repo. Exit 2 for
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

TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")
DOCUMENT = re.compile(r"\.(md|mdx|rst|txt|adoc)$", re.I)
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


def analyze(changes, keep, max_files=30, scoped=lambda path: True):
    """Change counts per file and shared-commit counts per pair, over the files `keep` accepts.
    A pair counts when at least one of its files is in scope. A bulk change counts for no pair:
    more than max_files files in scope for a pair inside it, more than max_files files in all
    for a pair with a partner outside."""
    revisions, shared, bulk = Counter(), Counter(), 0
    for files in changes:
        files = sorted({path for path in files if keep(path)})
        inside = [path for path in files if scoped(path)]
        if not inside:
            continue
        revisions.update(files)
        if len(inside) > max_files:
            bulk += 1
            continue
        shared.update(combinations(inside, 2))
        if len(files) <= max_files:
            shared.update(tuple(sorted((a, b))) for a in inside for b in files if not scoped(b))
    return revisions, shared, bulk


def kind(a, b):
    """What a pair is made of, so the reader can discount the expected ones: a test changes with its code."""
    if TEST_FILE.search(a) or TEST_FILE.search(b):
        return "test"
    return "document" if DOCUMENT.search(a) or DOCUMENT.search(b) else "code"


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
        tracked = set(git(args.repo, "ls-files").splitlines())
        in_scope = set(git(args.repo, "ls-files", "--", *args.paths).splitlines()) if args.paths else tracked
        log = git(args.repo, "log", f"--since={args.since}", "--no-merges", "--format=@%H", "--name-only")
        edges = read_edges(args.edges) if args.edges else None
    except (ValueError, OSError, re.error) as error:
        print(f"change_coupling: {error}", file=sys.stderr)
        return 2
    # A file that no longer exists cannot be reworked; its history stays out of the tables.
    keep = lambda path: path in tracked and not NOISE.search(path) and not any(p.search(path) for p in exclude)
    revisions, shared, bulk = analyze(commits(log), keep, args.max_files, scoped=in_scope.__contains__)
    touched = sum(1 for files in commits(log) if any(path in in_scope and keep(path) for path in files))
    print(f"History: {touched} commits since {args.since} changed the scope; {bulk} bulk commits (more than {args.max_files} files in scope) count for no pair.")
    if shallow:
        print("WARNING: this clone is shallow, so the counts cover only the fetched commits. "
              "Deepen it (git fetch --depth=<n>) or state the limit beside every count.")
    inside = [(path, count) for path, count in revisions.most_common() if path in in_scope]
    if not inside:
        print("No changed files in this window and scope.")
        return 0
    print(f"\nMost changed files in scope (top {args.top}):\n\nchanges\tfile")
    for path, count in inside[:args.top]:
        print(f"{count}\t{path}")
    rows = pairs(revisions, shared, args.min_shared)
    print(f"\nFiles that change together ({len(rows)} pairs with at least {args.min_shared} shared commits; top {args.top}).")
    print("degree: the share of the pair's changes that touched both files. kind: test and document pairs are often expected.")
    print("dependency: whether --edges holds an edge between the two; 'none found' with kind 'code' is the lead to one rule in two places.\n")
    print("shared\tdegree\tkind\tdirectories\tscope\tdependency\tpair")
    for count, degree, a, b in rows[:args.top]:
        across = "different" if PurePosixPath(a).parent != PurePosixPath(b).parent else "same"
        scope = "inside" if a in in_scope and b in in_scope else "one outside"
        linked = "not given" if edges is None else ("yes" if frozenset((a, b)) in edges else "none found")
        print(f"{count}\t{degree}%\t{kind(a, b)}\t{across}\t{scope}\t{linked}\t{a}  <->  {b}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # the reader, such as `head`, closed the pipe
        sys.exit(0)

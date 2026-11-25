#!/usr/bin/env python3
"""List the lines that handle one situation apart from the main path: leads to special cases.

A special case is code that exists for one situation: a broad error handler, an error turned
into a value or dropped, a default used when a value is missing, an early return on a missing
value, a retry or a sleep, a branch on a status code or version, a compatibility path, a
suppressed check. Each is a line to account for, not a defect: many are correct. Docstrings
are left out, and a comment gives a lead only for a compatibility path or a suppressed check.
A parameter that one caller sets, and a clamp, have no pattern: reading finds those. Patterns
cover common Python, JavaScript, TypeScript, Java, Kotlin, Go, Ruby, Rust, and C# idioms and
find leads, not every case. Run from the repository root, or pass --repo. Exit 2 for invalid
inputs or failed Git operations. No files are written.
"""
import argparse
from collections import Counter, defaultdict
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys

SOURCE = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".rb", ".rs", ".cs", ".php", ".swift", ".scala"}
TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")
TRIPLE = ('"' * 3, "'" * 3)
COMMENT = re.compile(r"^\s*(?:#|//|\*|/\*|--)")
HANDLER = re.compile(r"^\s*(?:\}\s*)?(?:except\b|catch\b|rescue\b)")
BROAD = re.compile(r"^\s*(?:\}\s*)?(?:except\s*:|except\s+\(?\s*(?:Base)?Exception\b|catch\s*\{"
                   r"|catch\s*\(\s*(?:final\s+)?(?:Exception|Throwable|RuntimeException|Error|e|err|error|ex|_)\b[^)]*\)"
                   r"|rescue\s*(?:$|=>|StandardError|Exception))|\brecover\(\)|\.catch\(\s*\(\s*\)\s*=>")
# The first statement of a handler that turns the failure into a value or drops it: nothing, a return, or a log line alone.
DROPS = re.compile(r"^\s*(?:pass\b|continue\b|\}\s*$|return\b|(?:log(?:ger)?|console|LOG)\.\w+\(.*\)\s*;?\s*$|print\w*\(.*\)\s*;?\s*$)")
MISSING = re.compile(r"^\s*(?:\}\s*)?(?:if|elif|else if)\b.*(?:\bis None\b|==\s*None\b|===?\s*(?:null|undefined)\b|==\s*nil\b"
                     r"|\bnot\s+\w[\w.]*\s*:|\(\s*!\w[\w.]*\s*\))")
LEAVES = re.compile(r"(?:return|continue)\b")
EMPTY = r"(?:\[\]|\{\}|''|\"\"|0\b|null\b|undefined\b|false\b|False\b|None\b)"
PATTERNS = {
    "default to an empty value": re.compile(rf"\?\?(?!=)\s*{EMPTY}|\|\|\s*{EMPTY}|\bor\s+{EMPTY}|\.get\(\s*[^(),]+,\s*{EMPTY}\s*\)"
                                            r"|\bunwrap_or_default\(|\bOptional\.ofNullable\("),
    "default to a named value": re.compile(rf"\?\?(?!=)\s*(?!{EMPTY})[\w\"']|\|\|\s*(?!{EMPTY})[A-Za-z_][\w.]*\s*[;,)]"
                                           rf"|=.*\bor\s+(?!{EMPTY})(?:self\.|this\.)?\w+(?:\.\w+)*\s*$|\.get\(\s*[^(),]+,\s*(?!{EMPTY})[^)]+\)"
                                           r"|\bgetattr\([^()]*,[^()]*,|\bgetOrDefault\(|\borElse(?:Get)?\(|\bunwrap_or(?:_else)?\(|\.fetch\([^()]*,[^()]*\)"),
    "retry or sleep": re.compile(r"\b(?:time\.)?sleep\(|\bThread\.sleep\(|\bsetTimeout\(|@retry\b|\bretry\("
                                 r"|\b(?:max_?(?:retries|attempts)|retries|attempts|backoff)\w*\s*(?:=|:|<|>)", re.I),
    "branch on a status code or version": re.compile(r"\bstatus(?:_?code)?\s*(?:===?|!==?|>=|<=|>|<|\bin\b)\s*\(?\s*[1-5]\d\d\b"
                                                     r"|version\w*[\"')\]]*\s*(?:===?|!==?|>=|<=|>|<)\s*[\"']?\d", re.I),
    "compatibility path": re.compile(r"\b(?:legacy|backwards?[- ]?compat\w*|compat(?:ibility)?\b|deprecated|fallback|fall back|workaround|shim"
                                     r"|for now|temporar\w+|hack)\b", re.I),
    "suppressed check": re.compile(r"@ts-ignore|@ts-expect-error|eslint-disable|biome-ignore|#\s*noqa|#\s*type:\s*ignore|pylint:\s*disable"
                                   r"|rubocop:disable|//\s*nolint|@SuppressWarnings|#\s*pragma:\s*no cover|#\[allow\("),
}
IN_COMMENTS_TOO = {"compatibility path", "suppressed check"}  # elsewhere a word in a comment is not the construct
ORDER = ("broad error handler", "error turned into a value or dropped", "early return on missing", *PATTERNS)


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def leads(lines):
    """(line number, kind, text) for each lead in one file's lines. Text inside a triple-quoted
    string is documentation or a prompt, not code, and gives no lead."""
    found, quoted = [], None
    for index, line in enumerate(lines):
        number, text = index + 1, line.strip()
        marks = [mark for mark in TRIPLE if line.count(mark) % 2]
        if quoted:
            quoted = None if quoted in marks else quoted
            continue
        if marks:
            quoted = marks[0]
            continue
        if not text or any(line.count(mark) for mark in TRIPLE):  # a one-line docstring
            continue
        following = next((other for other in lines[index + 1:index + 4] if other.strip()), "")
        if BROAD.search(line):
            found.append((number, "broad error handler", text))
        if HANDLER.match(line) and DROPS.match(following):
            found.append((number, "error turned into a value or dropped", f"{text}  ->  {following.strip()}"))
        condition = MISSING.match(line)
        if condition and (LEAVES.search(line[condition.end():]) or LEAVES.match(following.strip().lstrip("{ "))):
            found.append((number, "early return on missing", text))
        comment = bool(COMMENT.match(line))
        for kind, pattern in PATTERNS.items():
            if (not comment or kind in IN_COMMENTS_TOO) and pattern.search(line):
                found.append((number, kind, text))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="limit to these paths; default is the whole repository")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--tests", action="store_true", help="include test files, which are left out by default")
    parser.add_argument("--summary", action="store_true", help="print only the counts per kind and per file")
    args = parser.parse_args()
    try:
        files = git(args.repo, "ls-files", "--", *args.paths).splitlines()
    except ValueError as error:
        print(f"special_cases: {error}", file=sys.stderr)
        return 2
    by_kind, by_file, rows = Counter(), defaultdict(Counter), []
    for path in files:
        if PurePosixPath(path).suffix not in SOURCE or (not args.tests and TEST_FILE.search(path)):
            continue
        try:
            with open(os.path.join(args.repo, path), encoding="utf-8", errors="replace") as handle:
                lines = handle.read().splitlines()
        except OSError:
            continue
        for number, kind, text in leads(lines):
            by_kind[kind] += 1
            by_file[path][kind] += 1
            rows.append((kind, path, number, text))
    print(f"Leads to special cases: {sum(by_kind.values())} lines in {len(by_file)} files. Each is a line to account for, not a defect.\n")
    for kind in ORDER:
        print(f"{by_kind[kind]}\t{kind}")
    print("\nPer file (most leads first):\n")
    for path, counts in sorted(by_file.items(), key=lambda item: (-sum(item[1].values()), item[0])):
        detail = ", ".join(f"{counts[kind]} {kind}" for kind in ORDER if counts[kind])
        print(f"{sum(counts.values())}\t{path}\t{detail}")
    if not args.summary:
        for kind in ORDER:
            listed = [row for row in rows if row[0] == kind]
            if listed:
                print(f"\n## {kind} ({len(listed)})\n")
                for _, path, number, text in listed:
                    print(f"{path}:{number}\t{text[:160]}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # the reader, such as `head`, closed the pipe
        sys.exit(0)

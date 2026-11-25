#!/usr/bin/env python3
"""List the lines that handle one situation apart from the main path: leads to special cases.

A special case is code that exists for one situation: a broad or swallowed error handler, a
default used when a value is missing, an early return on a missing value, a retry or a sleep,
a compatibility path, a suppressed check. Each is a line to account for, not a defect: many
are correct. Patterns cover common Python, JavaScript, TypeScript, Java, Kotlin, Go, Ruby,
Rust, and C# idioms and find leads, not every case; reading the code finds the rest. Run
from the repository root, or pass --repo. Exit 2 for invalid inputs or failed Git operations.
No files are written.
"""
import argparse
from collections import Counter, defaultdict
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys

SOURCE = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".rb", ".rs", ".cs", ".php", ".swift", ".scala"}
HANDLER = re.compile(r"^\s*(?:\}\s*)?(?:except\b|catch\b|rescue\b)")
BROAD = re.compile(r"^\s*(?:\}\s*)?(?:except\s*:|except\s+\(?\s*(?:Base)?Exception\b|catch\s*\{|catch\s*\(\s*(?:final\s+)?(?:Exception|Throwable|RuntimeException|Error|e|err|error|ex|_)\b[^)]*\)"
                   r"|rescue\s*(?:$|=>|StandardError|Exception))|\brecover\(\)|\.catch\(\s*\(\s*\)\s*=>")
# The first statement of a handler that drops the failure: nothing, a constant, or a log line alone.
DROPS = re.compile(r"^\s*(?:pass\b|continue\b|\}\s*$|return\s*(?:None|null|nil|undefined|false|False|true|True|\[\]|\{\}|\"\"|''|0|Optional\.empty\(\))?\s*;?\s*$"
                   r"|(?:log(?:ger)?|console|LOG|log)\.\w+\(.*\)\s*;?\s*$|print\w*\(.*\)\s*;?\s*$)")
PATTERNS = {
    "default when missing": re.compile(r"\?\?(?!=)|\|\|\s*(?:\[\]|\{\}|''|\"\"|0\b|null\b|undefined\b|false\b)|\bor\s+(?:\[\]|\{\}|None\b|''|\"\"|0\b)"
                                       r"|\.get\(\s*[^(),]+,\s*[^)]+\)|\bgetattr\([^()]*,[^()]*,|\bgetOrDefault\(|\borElse(?:Get)?\(|\bunwrap_or(?:_default|_else)?\("
                                       r"|\.fetch\([^()]*,[^()]*\)|\bOptional\.ofNullable\("),
    "early return on missing": re.compile(r"^\s*if\s*\(?.*(?:\bis None\b|==\s*None\b|===?\s*(?:null|undefined)\b|==\s*nil\b|\bnot\s+\w[\w.]*\s*:|!\w[\w.]*\s*\))"
                                          r".*(?::\s*(?:return|continue)\b|\)\s*(?:return|continue)\b|\{\s*(?:return|continue)\b)"),
    "retry or sleep": re.compile(r"\b(?:retry|retries|retrying|backoff|max_attempts|maxAttempts)\b|\b(?:time\.)?sleep\(|\bThread\.sleep\(|\bsetTimeout\(", re.I),
    "compatibility path": re.compile(r"\b(?:legacy|backwards?[- ]?compat\w*|compat(?:ibility)?\b|deprecated|fallback|fall back|workaround|shim|for now|temporar\w+|hack)\b", re.I),
    "suppressed check": re.compile(r"@ts-ignore|@ts-expect-error|eslint-disable|biome-ignore|#\s*noqa|#\s*type:\s*ignore|pylint:\s*disable|rubocop:disable"
                                   r"|//\s*nolint|@SuppressWarnings|#\s*pragma:\s*no cover|#\[allow\("),
}
ORDER = ("broad error handler", "swallowed error", *PATTERNS)


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def leads(lines):
    """(line number, kind, text) for each lead in one file's lines."""
    found = []
    for index, line in enumerate(lines):
        number, text = index + 1, line.strip()
        if not text:
            continue
        if HANDLER.match(line) or BROAD.search(line):
            if BROAD.search(line):
                found.append((number, "broad error handler", text))
            body = next((other for other in lines[index + 1:index + 4] if other.strip()), "")
            if HANDLER.match(line) and DROPS.match(body):
                found.append((number, "swallowed error", f"{text}  ->  {body.strip()}"))
        for kind, pattern in PATTERNS.items():
            if pattern.search(line):
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
    test_file = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")
    by_kind, by_file, rows = Counter(), defaultdict(Counter), []
    for path in files:
        if PurePosixPath(path).suffix not in SOURCE or (not args.tests and test_file.search(path)):
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
    sys.exit(main())

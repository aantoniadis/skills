#!/usr/bin/env python3
"""List the values a change adds in more than one file: leads to one rule kept in several places.

A value is a word in quotes, a Ruby symbol, a word of a `%w` or `%i` list, or a number with a
decimal point or three or more digits. For the change from --base, this prints each value that
the added lines of two or more files hold, with those lines and the count of files that hold
the value as a word at the head. A kind, a status, a tier, or a rate that a change writes into
several files is often one rule decided in each of them, and a list of the same values in
several files is a registry kept by hand. A lead is a place to read, not a finding: a key of a
hash and a name used in a message repeat for good reason, and a string and a symbol of the same
word are counted as one value although the code may not treat them as one. A value built at
run time, and one spelled differently in each file, are not seen. The change runs from --base
to --head, or to the working tree with its untracked files when --head is not given. Test
files are left out unless --tests is given. Run from the repository root, or pass --repo.
Exit 2 for invalid inputs or failed Git operations. No files are written.
"""
import argparse
from collections import defaultdict
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys

SOURCE = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".rb", ".rake", ".rs", ".cs", ".php", ".swift", ".scala"}
TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")
COMMENT = re.compile(r"^\s*(?:#|//|\*|/\*|--)")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
QUOTED = re.compile(r"""(?<![\w\\])(?:"([^"\\\n]*)"|'([^'\\\n]*)')""")
SYMBOL = re.compile(r"(?<![\w:]):([a-z_]\w*[?!]?)(?![\w(:])")
WORD_LIST = re.compile(r"%[wi]\s*[\[({<]([^\])}>]*)[\])}>]")
NUMBER = re.compile(r"(?<![\w.])(\d+\.\d+|\d{3,})(?![\w.])")
VALUE = re.compile(r"[A-Za-z_][\w.-]{2,}|\d+\.\d+|\d{3,}")
COMMON = {"true", "false", "null", "none", "nil", "utf-8", "utf8", "__main__", "__init__", "self", "name", "value", "type", "error", "errors"}


def git(repo, *args, ok=(0,)):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode not in ok:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def added_text(diff):
    """(path, line number, text) for each line a unified diff with no context adds."""
    rows, path, number = [], None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = None if line == "+++ /dev/null" else line[4:].removeprefix("b/")
        elif line.startswith("@@"):
            match = HUNK.match(line)
            number = int(match.group(1)) if match else 0
        elif line.startswith("+") and path:
            rows.append((path, number, line[1:]))
            number += 1
    return rows


def values(line):
    """The values a code line holds, a string and a symbol of one word as the same value."""
    if COMMENT.match(line):
        return set()
    found = {first or second for first, second in QUOTED.findall(line)}
    found |= set(SYMBOL.findall(line)) | set(NUMBER.findall(line))
    for words in WORD_LIST.findall(line):
        found |= set(words.split())
    return {value for value in found if VALUE.fullmatch(value) and value.lower() not in COMMON}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="limit to these paths; default is the whole repository")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base", required=True, help="the commit the change starts from")
    parser.add_argument("--head", help="the commit that holds the change; default is the working tree")
    parser.add_argument("--tests", action="store_true", help="include test files, which are left out by default")
    parser.add_argument("--top", type=int, default=40, help="values to list")
    args = parser.parse_args()
    wanted = lambda path: PurePosixPath(path).suffix in SOURCE and (args.tests or not TEST_FILE.search(path))
    try:
        revisions = [args.base, args.head] if args.head else [args.base]
        rows = added_text(git(args.repo, "diff", "-U0", "--no-color", "--no-ext-diff", *revisions, "--", *args.paths))
        if not args.head:  # a file Git does not track yet is added as a whole
            for path in git(args.repo, "ls-files", "--others", "--exclude-standard", "--", *args.paths).splitlines():
                try:
                    with open(os.path.join(args.repo, path), encoding="utf-8", errors="replace") as handle:
                        rows += [(path, number, text) for number, text in enumerate(handle.read().splitlines(), 1)]
                except OSError:
                    continue
    except ValueError as error:
        print(f"added_values: {error}", file=sys.stderr)
        return 2
    sites = defaultdict(lambda: defaultdict(list))  # value -> path -> added lines that hold it
    for path, number, text in rows:
        if wanted(path):
            for value in values(text):
                sites[value][path].append(number)
    repeated = sorted(((value, by_file) for value, by_file in sites.items() if len(by_file) > 1), key=lambda item: (-len(item[1]), item[0]))
    target = f"{args.base} to {args.head}" if args.head else f"{args.base} to the working tree"
    print(f"Values added in more than one file from {target}: {len(repeated)} (top {args.top}). Each is a lead to one rule kept in several places.")
    for value, by_file in repeated[:args.top]:
        where = [args.head] if args.head else ["--untracked"]
        holders = git(args.repo, "grep", "-l", "-I", "-F", "-w", "-e", value, *where, "--", *args.paths, ok=(0, 1)).splitlines()
        holders = {line.split(":", 1)[1] if args.head else line for line in holders}
        count = sum(wanted(path) for path in holders)
        print(f"\n{value}\tadded in {len(by_file)} files; {count} files hold it at the head")
        print("\t" + ", ".join(f"{path}:{','.join(map(str, lines[:4]))}{'…' if len(lines) > 4 else ''}" for path, lines in sorted(by_file.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

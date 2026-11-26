#!/usr/bin/env python3
"""List the leads to shared mutable state, and the keys of untyped data passed between files.

Two tables. The first lists lines that keep state more than one piece of code can change: a
global, a class-level variable, a module-level collection, a thread or request context, a
memo. The second is a ledger of keys: for each string or symbol key of a hash, dict, or
object, the files that write it, the files that read it, and the reads that supply a default.
A key written in several files, read with a default, or read with different defaults is data
whose shape no one place declares. Leads, not findings: a key name is matched as text, so two
unrelated hashes that use the same key appear as one row; read the sites. Hash literals and
keyword arguments are not counted as writes. Patterns cover common Ruby, Python, JavaScript,
and TypeScript idioms, and static fields in Java, Kotlin, and C#. Run from the repository
root, or pass --repo. Exit 2 for invalid inputs or failed Git operations. No files are written.
"""
import argparse
from collections import defaultdict
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys

SOURCE = {".rb", ".rake", ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".cs", ".php"}
TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")
COMMENT = re.compile(r"^\s*(?:#|//|\*|/\*|--)")
STATE = {
    "global or class-level variable": re.compile(r"(?<![\w$])\$[a-z_]\w*\s*(?:\|\|)?=(?!=)|@@\w+\s*(?:\|\|)?=(?!=)|^\s*global\s+\w+"
                                                 r"|\b(?:cattr|mattr)_(?:accessor|writer)\b|\bclass_attribute\b|\b(?:globalThis|window)\.\w+\s*=(?!=)"
                                                 r"|^\s*(?:public|private|protected|internal)?\s*static\s+(?!final\b|readonly\b|const\b|class\b|void\b)"
                                                 r"[\w<>\[\],.? ]+\s+\w+\s*(?:=[^=]|;)"),
    "module-level collection": re.compile(r"^(?:[A-Za-z_]\w*)\s*(?::[^=]+)?=\s*(?:\{\}|\[\]|dict\(|list\(|set\(|defaultdict\(|OrderedDict\(|new (?:Map|Set)\()"
                                          r"|^(?:let|var)\s+\w+\s*=\s*(?:\{\}|\[\]|new (?:Map|Set)\()"),
    "thread or request context": re.compile(r"\bThread\.current\[|\bRequestStore\b|\bCurrent\.\w+\s*=(?!=)|\bContextVar\(|\bthreading\.local\(|\bThreadLocal\b"
                                            r"|\bAsyncLocalStorage\b"),
    "memo or cache": re.compile(r"@\w+\s*\|\|=|\b\w*cache\w*\s*(?:\|\|)?=\s*(?:\{\}|\[\]|Hash\.new|dict\(|new Map)|@(?:functools\.)?(?:lru_)?cache\b|\bmemoize\b", re.I),
}
KEY = r"""(?::(\w+[?!]?)|"([\w.\- ]+)"|'([\w.\- ]+)')"""
WRITE = re.compile(rf"\[\s*{KEY}\s*\]\s*(?:\|\||\+|-|<<)?=(?!=)|\.(?:store|setdefault)\(\s*{KEY}")
MERGE = re.compile(r"\.(?:deep_)?(?:merge|update)!?\(([^()]*)\)")
MERGE_KEY = re.compile(r"""(?:^|[,{\s])(\w+):\s|["']([\w.\- ]+)["']\s*(?:=>|:)""")
DEFAULTED = re.compile(rf"\.(?:fetch|get|pop)\(\s*{KEY}\s*,\s*([^()]*(?:\([^()]*\))?[^()]*)\)|\[\s*{KEY}\s*\]\s*(?:\|\||\?\?|\bor\b)\s*([^\s,;)]+)")
READ = re.compile(rf"\[\s*{KEY}\s*\](?!\s*(?:\|\||\+|-|<<)?=(?!=))|\.(?:fetch|get|dig|key\?|has_key\?|include\?)\(\s*{KEY}")


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def first(groups):
    return next((group for group in groups if group), None)


def state_leads(lines):
    """(line number, kind, text) for each line that keeps state several pieces of code can change."""
    return [(number, kind, line.strip()) for number, line in enumerate(lines, 1) if not COMMENT.match(line)
            for kind, pattern in STATE.items() if pattern.search(line)]


def key_uses(lines):
    """(line number, key, use, default) per key access; use is write, read, or default."""
    uses = []
    for number, line in enumerate(lines, 1):
        if COMMENT.match(line):
            continue
        claimed = set()
        for match in WRITE.finditer(line):
            uses.append((number, first(match.groups()), "write", None))
            claimed.add(match.start())
        for merged in MERGE.finditer(line):
            uses.extend((number, first(key), "write", None) for key in MERGE_KEY.findall(merged.group(1)))
        for match in DEFAULTED.finditer(line):
            groups = match.groups()
            key, default = first(groups[0:3]) or first(groups[4:7]), (groups[3] or groups[7] or "").strip()
            uses.append((number, key, "default", default))
            claimed.add(match.start())
        for match in READ.finditer(line):
            if match.start() not in claimed and not any(match.start() <= start < match.end() for start in claimed):
                uses.append((number, first(match.groups()), "read", None))
    return uses


def ledger(uses_by_file):
    """key -> {"write": {file: [lines]}, "read": {...}, "default": {...}, "defaults": {text}}"""
    keys = defaultdict(lambda: {"write": defaultdict(list), "read": defaultdict(list), "default": defaultdict(list), "defaults": set()})
    for path, uses in uses_by_file.items():
        for number, key, use, default in uses:
            keys[key][use][path].append(number)
            if use == "default" and default:
                keys[key]["defaults"].add(default)
    return keys


def notes(entry):
    """Why a key is worth reading: the signs that no one place declares it."""
    found = []
    readers = set(entry["read"]) | set(entry["default"])
    if len(entry["write"]) > 1:
        found.append(f"written in {len(entry['write'])} files")
    if entry["default"]:
        sites = sum(len(lines) for lines in entry["default"].values())
        found.append(f"read with a default at {sites} {'site' if sites == 1 else 'sites'}")
    if len(entry["defaults"]) > 1:
        found.append("defaults differ: " + " | ".join(sorted(entry["defaults"])))
    if entry["write"] and readers - set(entry["write"]):
        found.append("written in one file, read in another")
    if entry["write"] and not readers:
        found.append("written, never read here")
    return found


def sites(by_file):
    return ", ".join(f"{path}:{','.join(map(str, lines[:4]))}{'…' if len(lines) > 4 else ''}" for path, lines in sorted(by_file.items())) or "none here"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="limit to these paths; default is the whole repository")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--tests", action="store_true", help="include test files, which are left out by default")
    parser.add_argument("--top", type=int, default=40, help="keys to list")
    args = parser.parse_args()
    try:
        files = git(args.repo, "ls-files", "--", *args.paths).splitlines()
    except ValueError as error:
        print(f"shared_data: {error}", file=sys.stderr)
        return 2
    state, uses_by_file = [], {}
    for path in files:
        if PurePosixPath(path).suffix not in SOURCE or (not args.tests and TEST_FILE.search(path)):
            continue
        try:
            with open(os.path.join(args.repo, path), encoding="utf-8", errors="replace") as handle:
                lines = handle.read().splitlines()
        except OSError:
            continue
        state.extend((kind, path, number, text) for number, kind, text in state_leads(lines))
        uses_by_file[path] = key_uses(lines)
    print(f"Leads to shared mutable state: {len(state)} lines. Each is a line to read, not a defect.\n")
    for kind in STATE:
        listed = [row for row in state if row[0] == kind]
        if listed:
            print(f"## {kind} ({len(listed)})\n")
            for _, path, number, text in listed:
                print(f"{path}:{number}\t{text[:150]}")
            print()
    keys = {key: entry for key, entry in ledger(uses_by_file).items() if notes(entry)}
    ranked = sorted(keys.items(), key=lambda item: (-len(set(item[1]["write"]) | set(item[1]["read"]) | set(item[1]["default"])),
                                                    -len(item[1]["write"]), item[0]))
    print(f"Keys of untyped data: {len(keys)} keys with a sign that no one place declares them (top {args.top}).")
    print("A key is matched by name, so unrelated hashes that share a key share a row.\n")
    for key, entry in ranked[:args.top]:
        print(f"{key}\t{'; '.join(notes(entry))}")
        print(f"\twritten: {sites(entry['write'])}")
        print(f"\tread: {sites(entry['read'])}")
        if entry["default"]:
            print(f"\tread with a default: {sites(entry['default'])}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # the reader, such as `head`, closed the pipe
        sys.exit(0)

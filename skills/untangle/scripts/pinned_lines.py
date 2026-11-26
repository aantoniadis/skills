#!/usr/bin/env python3
"""Print the source text behind every pinned line in a note, to read against what the note says.

A pin is a Markdown link whose target ends in `#L12` or `#L12-L20`: a path relative to the
note, or a hosted blob URL with a commit, such as `.../blob/<sha>/src/app.py#L12`, which is
read from --repo with `git show`. The page checker confirms that a pin exists; it cannot tell
whether the line says what the sentence claims. This list makes that comparison quick: one
line per pin, with the link text and the source. A pin that cannot be read prints MISSING.
Exit 1 when any pin is missing, 2 for invalid inputs. No files are written.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

PIN = re.compile(r"\[([^\]]*)\]\(([^)\s]+?)#L(\d+)(?:-L?(\d+))?\)")
BLOB = re.compile(r"https?://[^/]+/[^/]+/[^/]+/(?:-/)?blob/([0-9a-fA-F]{7,40})/(.+)")


def read_lines(target, note, repo):
    """The lines of a pinned file, or None when it cannot be read."""
    blob = BLOB.match(target)
    if blob:
        if repo is None:
            return None
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        result = subprocess.run(["git", "-C", str(repo), "show", f"{blob.group(1)}:{unquote(blob.group(2))}"],
                                env=env, capture_output=True, text=True, errors="replace")
        return result.stdout.splitlines() if result.returncode == 0 else None
    if "://" in target:
        return None
    try:
        return (note.parent / unquote(target)).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None


def pins(source):
    """(note line, link text, target, first, last) for each pin outside fenced code."""
    fenced = False
    for number, line in enumerate(source.splitlines(), 1):
        if re.match(r"\s*(`{3,}|~{3,})", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for match in PIN.finditer(line):
            first = int(match.group(3))
            yield number, match.group(1), match.group(2), first, int(match.group(4) or first)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("note", type=Path)
    parser.add_argument("--repo", type=Path, help="the checkout that holds the commits of hosted pins")
    args = parser.parse_args()
    try:
        source = args.note.read_text(encoding="utf-8")
    except OSError as error:
        print(f"pinned_lines: {error}", file=sys.stderr)
        return 2
    cache, missing, count = {}, 0, 0
    for number, text, target, first, last in pins(source):
        count += 1
        if target not in cache:
            cache[target] = read_lines(target, args.note, args.repo)
        lines = cache[target]
        name = unquote(target).rsplit("/", 1)[-1]
        if lines is None or first < 1 or last > len(lines):
            missing += 1
            print(f"note:{number}\t[{text}]\t{name}:{first}\tMISSING")
            continue
        shown = " ⏎ ".join(line.strip() for line in lines[first - 1:min(last, first + 2)])
        more = f" … (+{last - first - 2} lines)" if last - first > 2 else ""
        print(f"note:{number}\t[{text}]\t{name}:{first}{'-' + str(last) if last != first else ''}\t{shown[:200]}{more}")
    print(f"pinned_lines: {count} pins, {missing} missing", file=sys.stderr)
    return 1 if missing else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # the reader, such as `head`, closed the pipe
        sys.exit(0)

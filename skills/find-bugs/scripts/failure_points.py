#!/usr/bin/env python3
"""List the lines a change adds that can fail at run time, between two commits.

A failure point is a call that touches the world outside the process: it opens,
reads, writes, closes, renames, deletes, links, locks, spawns, or connects. Each is
a place to make the change fail part-way and see what state remains. Patterns cover
common Python, JavaScript, TypeScript, Go, Rust, Java, and Ruby idioms; they find
leads, not every call. Run from the repository root, or pass --repo. Exit 2 for
invalid inputs or failed Git operations. No files are written.
"""
import argparse
import os
from pathlib import PurePosixPath
import re
import subprocess

CALLS = re.compile(
    r"\b(open|fdopen|close|read|write|flush|fsync|fdatasync|ftruncate|truncate|unlink|remove|rename|replace|link|symlink"
    r"|hardlink_to|symlink_to|mkdir|makedirs|rmdir|rmtree|chmod|chown|utime|stat|lstat|fstat|lockf|flock|scandir|listdir"
    r"|read_text|write_text|read_bytes|write_bytes|touch|copy|copy2|copyfile|move|mkstemp|mkdtemp|NamedTemporaryFile"
    r"|Popen|run|check_output|check_call|spawn|exec|execFile|fork|connect|bind|listen|accept|send|recv|urlopen|request"
    r"|fetch|readFile|writeFile|appendFile|readFileSync|writeFileSync|renameSync|unlinkSync|mkdirSync|rmSync|openSync"
    r"|closeSync|createReadStream|createWriteStream|Create|OpenFile|ReadFile|WriteFile|Remove|RemoveAll|Rename|Mkdir"
    r"|MkdirAll|Symlink|Link|Command|Dial|Listen)\s*\(")
QUALIFIED = re.compile(r"\b(os|shutil|subprocess|socket|tempfile|fcntl|msvcrt|fs|fsp|child_process|net|http|https"
                       r"|ioutil|io|exec|syscall|File|Files|FileUtils|IO|std::fs|std::net|std::process)\b\s*(\.|::)")
COMMENT = re.compile(r"^\s*(#|//|\*|/\*|--)")
SOURCE = {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".rb"}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
DEFINITION = re.compile(r"^\s*(?:async\s+)?(?:def|function|func|fn|sub)\s+(?:\([^)]*\)\s*)?([A-Za-z_$][\w$]*)"
                        r"|^\s*(?:public|private|protected|static|final|\s)*[\w<>\[\],.?]+\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{")


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def enclosing(lines, number):
    for text in reversed(lines[:number]):
        match = DEFINITION.match(text)
        if match:
            return match.group(1) or match.group(2)
    return ""


def points(diff, source=lambda path: []):
    found, path, new, lines = [], None, 0, []
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = None if line == "+++ /dev/null" else line[4:].removeprefix("b/")
            lines = source(path) if path else []
            continue
        if line.startswith(("--- ", "diff --git ")):
            continue
        match = HUNK.match(line)
        if match:
            new = int(match.group(1))
            continue
        if path is None or not line.startswith("+"):
            continue
        text = line[1:]
        is_source = PurePosixPath(path).suffix.lower() in SOURCE and "test" not in PurePosixPath(path).name.lower()
        if is_source and not COMMENT.match(text) and (CALLS.search(text) or QUALIFIED.search(text)):
            found.append((path, new, enclosing(lines, new), text.strip()))
        new += 1
    return found


def report(found):
    if not found:
        return "No added line matches a failure-point pattern."
    lines, last = [f"{len(found)} added lines can fail at run time:"], None
    for path, number, context, text in found:
        if path != last:
            lines.append(f"\n## {path}")
            last = path
        where = f" in `{context}`" if context else ""
        lines.append(f"- `{path}:{number}`{where} `{text[:110]}`")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    try:
        diff = git(args.repo, "diff", "--unified=0", "--no-color", "--no-ext-diff", f"{args.base}..{args.head}")
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    def source(path):
        try:
            return git(args.repo, "show", f"{args.head}:{path}").splitlines()
        except ValueError:
            return []
    print(report(points(diff, source)))


if __name__ == "__main__":
    main()

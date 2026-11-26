#!/usr/bin/env python3
"""Break decisions one at a time in a scratch worktree and record which tests notice.

Each row of the breaks file names one break: a short name, a file, a line number, the text that
replaces that line, and the focused test command expected to catch it. The script makes a
disposable worktree of HEAD, runs --setup once there, then for each break replaces the line,
runs the focused command, and restores the line. A break the focused tests did not catch is run
again under --full, because a focused selection can miss a test that does protect the behavior:
per-test coverage, for one, can miss lines such as `await` expressions. Only a break that stays
green under --full is reported as behavior no test protects.

    break_probe.py breaks.tsv --full "uv run pytest tests -q" --setup "uv sync" --out runs/breaks

Breaks file, tab-separated, one break per line, `#` for comments:

    name<TAB>path<TAB>line<TAB>replacement line<TAB>focused test command

The worktree holds HEAD; uncommitted changes in the checkout are not in it. Commands run with
the worktree as their working directory, through the shell. Logs go under --out, one per run.
The worktree is removed at the end. Exit 1 when a line does not match its file, 2 for invalid
inputs or failed Git operations.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def read_breaks(path):
    breaks = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 5 or not parts[2].strip().isdigit():
            raise ValueError(f"{path}:{number}: give name, path, line, replacement, and focused command, tab-separated")
        name, target, line_number, replacement, command = parts
        breaks.append({"name": name.strip(), "path": target.strip(), "line": int(line_number), "replacement": replacement, "command": command.strip()})
    return breaks


STAMP = [time.time()]


def write(target, text):
    """Write and give the file a new modification time. A break and its restore often have the same size and
    land within one second, and a cache keyed on size and time, such as Python's bytecode, would keep the
    other version."""
    target.write_text(text, encoding="utf-8")
    STAMP[0] = max(STAMP[0] + 2, time.time())
    os.utime(target, (STAMP[0], STAMP[0]))


def run(command, cwd, log, timeout):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        code, output = result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as error:
        code, output = 124, f"timed out after {timeout} s\n{error.stdout or ''}{error.stderr or ''}"
    log.write_text(f"$ {command}\nexit {code}\n\n{output}")
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("breaks", help="tab-separated breaks file")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--full", required=True, help="the command that runs every test of the scope")
    parser.add_argument("--setup", help="a command to run once in the worktree first, such as installing dependencies")
    parser.add_argument("--out", required=True, help="directory for the run logs")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per command")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    try:
        breaks = read_breaks(args.breaks)
        root = git(args.repo, "rev-parse", "--show-toplevel").strip()
        head = git(args.repo, "rev-parse", "HEAD").strip()
    except (OSError, ValueError) as error:
        print(f"break_probe: {error}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    worktree = Path(tempfile.mkdtemp(prefix="break-probe-")) / "tree"
    try:
        git(root, "worktree", "add", "--detach", str(worktree), head)
    except ValueError as error:
        print(f"break_probe: {error}", file=sys.stderr)
        return 2
    mismatched, rows = 0, []
    try:
        if args.setup and run(args.setup, worktree, out / "setup.log", args.timeout):
            print(f"break_probe: setup failed; see {out / 'setup.log'}", file=sys.stderr)
            return 2
        for index, item in enumerate(breaks, 1):
            target = worktree / item["path"]
            try:
                original = target.read_text(encoding="utf-8")
            except OSError:
                rows.append((item, "missing file", "", "")); mismatched += 1
                continue
            lines = original.splitlines(keepends=True)
            if not 1 <= item["line"] <= len(lines):
                rows.append((item, "no such line", "", "")); mismatched += 1
                continue
            old = lines[item["line"] - 1]
            ending = old[len(old.rstrip("\r\n")):] or "\n"
            lines[item["line"] - 1] = item["replacement"] + ending
            write(target, "".join(lines))
            try:
                focused = run(item["command"], worktree, out / f"{index:02d}-focused.log", args.timeout)
                full = None if focused else run(args.full, worktree, out / f"{index:02d}-full.log", args.timeout)
            finally:
                write(target, original)
            rows.append((item, "focused red" if focused else ("full red" if full else "green"), old.strip(), index))
    finally:
        subprocess.run(["git", "-C", root, "worktree", "remove", "--force", str(worktree)], capture_output=True)
        subprocess.run(["rm", "-rf", str(worktree.parent)], capture_output=True)
    meaning = {"focused red": "pinned: the focused tests catch it",
               "full red": "pinned, but only outside the focused tests: widen the selection that protects it",
               "green": "no test protects it",
               "missing file": "the file is not in HEAD", "no such line": "the line number is past the end of the file"}
    print(f"Breaks at {head[:12]}: {len(rows)}. Logs: {out}\n")
    print("result\tbreak\tat\toriginal line\tmeaning")
    for item, result, old, index in rows:
        print(f"{result}\t{item['name']}\t{item['path']}:{item['line']}\t{old[:80]}\t{meaning[result]}")
    green = sum(1 for _, result, _, _ in rows if result == "green")
    print(f"\n{green} of {len(rows)} breaks left every test green under the full command.")
    return 1 if mismatched else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # the reader, such as `head`, closed the pipe
        sys.exit(0)

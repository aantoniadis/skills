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

The worktree holds HEAD. Pass --with-local-changes to bring the checkout's uncommitted changes
into it, tracked edits and untracked files that Git does not ignore: a lock test is written
before it is committed, and without it the worktree has no such test. Line numbers are then those
of the working tree. Each focused command runs once on the unbroken worktree first, as a control,
and so does the full command the first time a break reaches it: a command that already fails
there, because its test is missing, the setup is incomplete, or a test fails before any break, is
reported as *red before the break* and pins nothing. Commands run with the worktree as their
working directory, through the shell. Logs go under --out, one per run. The worktree is removed
at the end. Exit 1 when a line does not match its file or a control fails, 2 for invalid inputs
or failed Git operations.
"""
import argparse
import os
from pathlib import Path
import shutil
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


def copy_local_changes(root, worktree, skip):
    """Apply the checkout's tracked edits to the worktree and copy its untracked files, except those under `skip`."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    patch = subprocess.run(["git", "-C", root, "diff", "HEAD", "--binary"], env=env, capture_output=True)
    if patch.returncode:
        raise ValueError(patch.stderr.decode(errors="replace").strip())
    if patch.stdout:
        applied = subprocess.run(["git", "-C", str(worktree), "apply", "--binary", "-"], env=env, input=patch.stdout, capture_output=True)
        if applied.returncode:
            raise ValueError(applied.stderr.decode(errors="replace").strip())
    for name in git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        source = Path(root) / name
        if not name or not source.is_file() or skip in source.resolve().parents:
            continue
        target = worktree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


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
    parser.add_argument("--with-local-changes", action="store_true",
                        help="bring the checkout's uncommitted changes into the worktree, such as lock tests not yet committed")
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
    mismatched, rows, controls, full_control = 0, [], {}, None  # controls: a command's exit code on the unbroken worktree
    try:
        if args.with_local_changes:
            try:
                copy_local_changes(root, worktree, out)
            except (OSError, ValueError) as error:
                print(f"break_probe: the uncommitted changes do not apply to HEAD: {error}", file=sys.stderr)
                return 2
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
            if item["command"] not in controls:
                controls[item["command"]] = run(item["command"], worktree, out / f"control-{index:02d}.log", args.timeout)
            if controls[item["command"]]:
                rows.append((item, "red before the break", old.strip(), index)); mismatched += 1
                continue
            ending = old[len(old.rstrip("\r\n")):] or "\n"
            lines[item["line"] - 1] = item["replacement"] + ending
            broken = "".join(lines)
            write(target, broken)
            try:
                focused = run(item["command"], worktree, out / f"{index:02d}-focused.log", args.timeout)
                if focused:
                    result = "focused red"
                else:
                    if full_control is None:  # once, on the unbroken worktree, the first time a break reaches the full command
                        write(target, original)
                        full_control = run(args.full, worktree, out / "control-full.log", args.timeout)
                        write(target, broken)
                    if full_control:
                        result = "full red before the break"
                        mismatched += 1
                    else:
                        result = "full red" if run(args.full, worktree, out / f"{index:02d}-full.log", args.timeout) else "green"
            finally:
                write(target, original)
            rows.append((item, result, old.strip(), index))
    finally:
        subprocess.run(["git", "-C", root, "worktree", "remove", "--force", str(worktree)], capture_output=True)
        subprocess.run(["rm", "-rf", str(worktree.parent)], capture_output=True)
    meaning = {"focused red": "pinned: the focused tests catch it",
               "full red": "pinned, but only outside the focused tests: widen the selection that protects it",
               "green": "no test protects it",
               "red before the break": "the focused command fails on the unbroken worktree, so it pins nothing: see its control log",
               "full red before the break": "the full command fails on the unbroken worktree, so it cannot show a pin: "
                                            "fix or leave out what already fails; see control-full.log",
               "missing file": "the file is not in the worktree", "no such line": "the line number is past the end of the file"}
    local = " with the checkout's uncommitted changes" if args.with_local_changes else ""
    print(f"Breaks at {head[:12]}{local}: {len(rows)}. Logs: {out}\n")
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

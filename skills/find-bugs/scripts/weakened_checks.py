#!/usr/bin/env python3
"""List the places where a change weakened its own checks, between two commits.

Leads, not verdicts: added suppressions, skipped or focused tests, removed tests and
assertions, unimplemented stubs, and edited coverage or threshold configuration.
Patterns cover common JavaScript, TypeScript, Python, Go, Rust, Java, Ruby, and PHP
idioms; a language outside that list gets only the configuration leads. Run from the
repository root, or pass --repo. Exit 2 for invalid inputs or failed Git operations.
No files are written.
"""
import argparse
import os
from pathlib import PurePosixPath
import re
import subprocess

ADDED = {
    "suppression": re.compile(r"@ts-ignore|@ts-expect-error|eslint-disable|biome-ignore|#\s*noqa|#\s*type:\s*ignore"
                              r"|pylint:\s*disable|rubocop:disable|phpcs:ignore|//\s*nolint|#pragma warning disable|@SuppressWarnings"),
    "skipped or focused test": re.compile(r"\.(skip|only|todo)\(|\b(xit|xdescribe|xtest|fit|fdescribe)\(|@pytest\.mark\.skip|@unittest\.skip"
                                          r"|pytest\.skip\(|\bt\.Skip\(|@Disabled\b|@Ignore\b|#\[ignore\]|\bskip:\s*true"),
    "stub": re.compile(r"NotImplementedError|unimplemented!\(|todo!\(|not implemented|\bUnsupportedOperationException\b"),
}
REMOVED = {
    "removed test": re.compile(r"^\s*(async\s+)?(def\s+test_|it\(|test\(|describe\(|func\s+Test\w*\(|@Test\b|#\[test\]|it\s+['\"])"),
    "removed assertion": re.compile(r"^\s*(assert\w*\b|expect\(|self\.assert\w*\(|require\.\w+\(|t\.(Fatal|Error)f?\(|\w+\.should\b)"),
}
THRESHOLD_FILES = re.compile(r"(^|/)(jest|vitest|karma)\.config\.\w+$|(^|/)(\.coveragerc|pyproject\.toml|setup\.cfg|tox\.ini|codecov\.ya?ml"
                             r"|\.codecov\.ya?ml|\.nycrc(\.\w+)?|sonar-project\.properties|package\.json)$")
THRESHOLD_LINE = re.compile(r"threshold|fail_under|fail-under|cov-fail|coverage|branches|functions|statements|\blines\b|minimum", re.I)
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def leads(diff):
    found, path, old, new, header = [], None, 0, 0, False
    for line in diff.splitlines():
        # File headers sit between `diff --git` and the first hunk; inside a hunk,
        # a removed `-- comment` line also starts with `--- `.
        if line.startswith("diff --git "):
            header, path = True, None
            continue
        if header and line.startswith("--- "):
            path = None if line == "--- /dev/null" else line[4:].removeprefix("a/")
            continue
        if header and line.startswith("+++ "):
            if line != "+++ /dev/null":  # a deleted file keeps its old path
                path = line[4:].removeprefix("b/")
            continue
        match = HUNK.match(line)
        if match:
            header, old, new = False, int(match.group(1)), int(match.group(2))
            continue
        if header or path is None or not line or line[0] not in "+-":
            continue
        text = line[1:]
        config = bool(THRESHOLD_FILES.search(str(PurePosixPath(path))))
        if line[0] == "+":
            for kind, pattern in ADDED.items():
                if pattern.search(text):
                    found.append((kind, path, new, "+" + text.strip()))
            if config and THRESHOLD_LINE.search(text):
                found.append(("threshold or coverage configuration changed", path, new, "+" + text.strip()))
            new += 1
        else:
            for kind, pattern in REMOVED.items():
                if pattern.search(text):
                    found.append((kind, path, old, "-" + text.strip()))
            if config and THRESHOLD_LINE.search(text):
                found.append(("threshold or coverage configuration changed", path, old, "-" + text.strip()))
            old += 1
    return found


def report(found):
    if not found:
        return "No weakened checks found between the two commits by these patterns."
    lines = []
    for kind in dict.fromkeys(k for k, *_ in found):
        lines.append(f"## {kind}")
        lines += [f"- `{path}:{number}` `{text[:120]}`" for k, path, number, text in found if k == kind]
        lines.append("")
    return "\n".join(lines).rstrip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    try:
        diff = git(args.repo, "diff", "--unified=0", "--no-color", f"{args.base}..{args.head}")
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(report(leads(diff)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Write the import edges between a repository's own files, as `from<TAB>to` lines.

A floor for the dependency map when no compiler, language server, or dependency tool gives
edges: it reads static import statements in Python, JavaScript, TypeScript, and Java, and
keeps the ones that resolve to a tracked file. It misses dynamic imports, dependency
injection, reflection, and string-keyed lookups, and every other language, so an absent edge
proves nothing. Confirm an edge that decides a conclusion at its source line. Run from the
repository root, or pass --repo. Exit 2 for invalid inputs or failed Git operations. Output
goes to stdout; no files are written.
"""
import argparse
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys

PYTHON = re.compile(r"^\s*(?:from\s+(\.*[\w.]*)\s+import\s+(.+)|import\s+([\w., ]+))")
SCRIPT = re.compile(r"""(?:\bfrom\s+|\bimport\s*\(\s*|\brequire\s*\(\s*|^\s*import\s+)['"]([^'"]+)['"]""")
JAVA = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+?)(?:\.\*)?\s*;")
SCRIPT_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def python_modules(files):
    """Dotted module name -> files, for every suffix of each path: `a/src/pkg/mod.py` answers to
    `pkg.mod` as well as `a.src.pkg.mod`, because the import root is not known."""
    modules = {}
    for path in files:
        if not path.endswith(".py"):
            continue
        parts = list(PurePosixPath(path).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        for start in range(len(parts)):
            modules.setdefault(".".join(parts[start:]), []).append(path)
    return modules


def nearest(importer, candidates, name):
    """The candidate that shares the longest directory prefix with the importer. A one-word name
    such as `config` resolves only to a file under a shared directory: elsewhere it is more
    likely an installed package of the same name."""
    here = PurePosixPath(importer).parent.parts
    def shared(path):
        there = PurePosixPath(path).parent.parts
        return next((i for i, (a, b) in enumerate(zip(here, there)) if a != b), min(len(here), len(there)))
    best = max(sorted(candidates), key=shared)
    return best if "." in name or shared(best) else None


def python_edges(path, text, modules):
    package = list(PurePosixPath(path).parent.parts)
    for line in text.splitlines():
        match = PYTHON.match(line)
        if not match:
            continue
        if match.group(3):  # import a.b, c
            names = [name.split(" as ")[0].strip() for name in match.group(3).split(",")]
        else:  # from a.b import c: c is the module a.b.c or a member of a.b
            base, imported = match.group(1), match.group(2)
            dots = len(base) - len(base.lstrip("."))
            if dots:  # relative: resolve against this file's package
                anchor = package[:len(package) - (dots - 1)] if dots > 1 else package
                base = ".".join([*anchor, base.lstrip(".")]).strip(".")
            members = [name.split(" as ")[0].strip(" ()\\") for name in imported.split(",")]
            names = [f"{base}.{member}" if f"{base}.{member}" in modules else base
                     for member in members if member and member != "*"] or [base]
        for name in dict.fromkeys(names):
            target = nearest(path, modules[name], name) if name in modules else None
            if target:
                yield target


def script_edges(path, text, files):
    folder = PurePosixPath(path).parent
    for target in SCRIPT.findall(text):
        if not target.startswith("."):
            continue  # a package or an alias: outside this floor
        base = os.path.normpath(str(folder / target)).replace(os.sep, "/")
        candidates = [base, *(base + suffix for suffix in SCRIPT_SUFFIXES),
                      *(f"{base}/index{suffix}" for suffix in SCRIPT_SUFFIXES)]
        if base.endswith(".js"):  # TypeScript sources imported under their emitted name
            candidates += [base[:-3] + ".ts", base[:-3] + ".tsx"]
        found = next((candidate for candidate in candidates if candidate in files), None)
        if found:
            yield found


def java_classes(files):
    classes = {}
    for path in files:
        if path.endswith((".java", ".kt")):
            parts = PurePosixPath(path).with_suffix("").parts
            for start in range(len(parts)):
                classes.setdefault(".".join(parts[start:]), path)
    return classes


def java_edges(text, classes):
    for line in text.splitlines():
        match = JAVA.match(line)
        if match and match.group(1) in classes:
            yield classes[match.group(1)]


def edges(repo, files):
    files = set(files)
    modules, classes = python_modules(sorted(files)), java_classes(sorted(files))
    found = set()
    for path in sorted(files):
        suffix = PurePosixPath(path).suffix
        if suffix not in (".py", ".java", ".kt", *SCRIPT_SUFFIXES):
            continue
        try:
            with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            continue
        if suffix == ".py":
            targets = python_edges(path, text, modules)
        elif suffix in SCRIPT_SUFFIXES:
            targets = script_edges(path, text, files)
        else:
            targets = java_edges(text, classes)
        found.update((path, target) for target in targets if target != path)
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="limit to these paths; default is the whole repository")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    try:
        files = git(args.repo, "ls-files", "--", *args.paths).splitlines()
    except ValueError as error:
        print(f"import_edges: {error}", file=sys.stderr)
        return 2
    rows = edges(args.repo, files)
    print("# from\tto  (static imports that resolve to a tracked file; an absent edge proves nothing)")
    for source, target in rows:
        print(f"{source}\t{target}")
    print(f"import_edges: {len(rows)} edges from {len(files)} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

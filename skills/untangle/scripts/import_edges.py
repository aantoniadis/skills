#!/usr/bin/env python3
"""Write the import edges between a repository's own files, as `from<TAB>to` lines.

A floor for the dependency map when no compiler, language server, or dependency tool gives
edges. It reads static import statements in Python, JavaScript, TypeScript, and Java, and in
Ruby `require_relative` and references to a constant that one file defines, and keeps the ones
that resolve to a tracked file. Edges that start in a test file are left out unless --tests is
given. It misses dynamic imports, dependency injection, reflection, string-keyed lookups, a
Ruby constant that several files define, and every other language, so an absent edge proves
nothing; and it reports an import used only for type checking as an ordinary edge. Confirm an
edge that decides a conclusion at its source line.

With --rev, the edges are read at that commit. With --base, only the edges a change adds are
printed, from that commit to --head, or to the working tree with its untracked files when
--head is not given. Each added edge carries what it changes in the map: a cycle it closes
between files, and the first dependency of one directory on another, with a note when the two
directories then depend on each other. These are leads to read, not findings.

Run from the repository root, or pass --repo. Exit 2 for invalid inputs or failed Git
operations. Output goes to stdout; no files are written.
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
RUBY_UNIT = re.compile(r"^(\s*)(?:module|class)\s+([A-Z][\w:]*)")
RUBY_REQUIRE = re.compile(r"""^\s*require_relative\s+['"]([^'"]+)['"]""")
RUBY_CONSTANT = re.compile(r"(?<![\w:.@$])(?:::)?[A-Z]\w*(?:::[A-Z]\w*)*")
RUBY_CONTENT = re.compile(r"^\s*(?:def\b|[A-Z][A-Z0-9_]*\s*=(?!=)|(?:extend|include|prepend|attr_\w+)\b)")
RUBY_STRING = re.compile(r"""\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*'""")
TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")


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


def ruby_scan(text):
    """The units a Ruby file gives content to, and its code lines with the units that enclose each.
    Read by indentation: a unit ends at the `end` that has the indentation of its first line. A unit
    that only encloses other units, as a namespace does, is not counted as defined here."""
    defined, lines, open_units = {}, [], []  # open_units: (indent, qualified name)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if open_units and indent == open_units[-1][0] and stripped.split("#")[0].strip() == "end":
            open_units.pop()
            continue
        code = RUBY_STRING.sub('""', line).split("#")[0]
        nesting = tuple(name for _, name in open_units)
        start = RUBY_UNIT.match(line)
        if start:
            name = f"{nesting[-1]}::{start.group(2)}" if nesting else start.group(2)
            defined.setdefault(name, "<" in code)  # a superclass is content
            open_units.append((indent, name))
            lines.append((nesting, code[start.end(2):]))  # the superclass is a reference; the name is not
            continue
        if nesting and RUBY_CONTENT.match(line):
            defined[nesting[-1]] = True
        lines.append((nesting, code))
    return {name for name, content in defined.items() if content}, lines


def ruby_constants(scans):
    """Constant name -> the one file that gives it content. A name several files define resolves to none."""
    owners = {}
    for path, (defined, _) in scans.items():
        for name in defined:
            owners.setdefault(name, []).append(path)
    return {name: paths[0] for name, paths in owners.items() if len(paths) == 1}


def ruby_edges(path, text, lines, constants, files):
    folder = PurePosixPath(path).parent
    for line in text.splitlines():
        required = RUBY_REQUIRE.match(line)
        if required:
            target = os.path.normpath(str(folder / required.group(1))).replace(os.sep, "/")
            target = target if target.endswith(".rb") else target + ".rb"
            if target in files:
                yield target
    for nesting, code in lines:
        for reference in RUBY_CONSTANT.findall(code):
            absolute, parts = reference.startswith("::"), reference.lstrip(":").split("::")
            scopes = [""] if absolute else [*reversed(nesting), ""]  # the innermost enclosing unit first, as Ruby looks a name up
            for scope in scopes:
                found = next((constants[name] for size in range(len(parts), 0, -1)
                              for name in [f"{scope}::{'::'.join(parts[:size])}".lstrip(":")] if name in constants), None)
                if found:
                    yield found
                    break


def edges(read, files):
    """The edges between the given files; read(path) returns a file's text, or None."""
    files = set(files)
    modules, classes = python_modules(sorted(files)), java_classes(sorted(files))
    texts = {path: read(path) for path in sorted(files) if PurePosixPath(path).suffix in (".py", ".java", ".kt", ".rb", *SCRIPT_SUFFIXES)}
    texts = {path: text for path, text in texts.items() if text is not None}
    scans = {path: ruby_scan(text) for path, text in texts.items() if path.endswith(".rb")}
    constants = ruby_constants(scans)
    found = set()
    for path, text in texts.items():
        suffix = PurePosixPath(path).suffix
        if suffix == ".py":
            targets = python_edges(path, text, modules)
        elif suffix == ".rb":
            targets = ruby_edges(path, text, scans[path][1], constants, files)
        elif suffix in SCRIPT_SUFFIXES:
            targets = script_edges(path, text, files)
        else:
            targets = java_edges(text, classes)
        found.update((path, target) for target in targets if target != path)
    return sorted(found)


def working_tree(repo):
    def read(path):
        try:
            with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as handle:
                return handle.read()
        except OSError:
            return None
    return read


def at_revision(repo, revision, files):
    """A reader of the given files at a commit, through one `git cat-file --batch` call."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    wanted = [path for path in files if PurePosixPath(path).suffix in (".py", ".java", ".kt", ".rb", *SCRIPT_SUFFIXES)]
    result = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], env=env, capture_output=True,
                            input="".join(f"{revision}:{path}\n" for path in wanted).encode())
    texts, data, position = {}, result.stdout, 0
    for path in wanted:
        end = data.find(b"\n", position)
        if end < 0:
            break
        header = data[position:end].split()
        position = end + 1
        if len(header) == 3 and header[1] == b"blob":
            size = int(header[2])
            texts[path] = data[position:position + size].decode("utf-8", errors="replace")
            position += size + 1
    return texts.get


def chain(start, goal, graph):
    """The shortest path of edges from start to goal, as a list of files, or None."""
    seen, queue = {start: None}, [start]
    for node in queue:
        if node == goal:
            path = []
            while node is not None:
                path.append(node)
                node = seen[node]
            return path[::-1]
        for following in sorted(graph.get(node, ())):
            if following not in seen:
                seen[following] = node
                queue.append(following)
    return None


def added(base_edges, head_edges):
    """(from, to, notes) for each edge the head has and the base lacks."""
    graph, directory = {}, lambda path: str(PurePosixPath(path).parent)
    for source, target in head_edges:
        graph.setdefault(source, set()).add(target)
    between = lambda pairs: {(directory(a), directory(b)) for a, b in pairs if directory(a) != directory(b)}
    base_directories, head_directories = between(base_edges), between(head_edges)
    rows, cycles = [], set()
    for source, target in sorted(set(head_edges) - set(base_edges)):
        notes, back = [], chain(target, source, graph)
        if back and frozenset(back) in cycles:
            notes.append("in the cycle above")
        elif back:
            cycles.add(frozenset(back))
            notes.append("closes a cycle: " + " -> ".join([*back, target]))
        pair = (directory(source), directory(target))
        if pair[0] != pair[1] and pair not in base_directories:
            note = f"first dependency of {pair[0]}/ on {pair[1]}/"
            if pair[::-1] in head_directories:
                note += f"; {pair[1]}/ depends on {pair[0]}/ too"
            notes.append(note)
        rows.append((source, target, "; ".join(notes)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="limit to these paths; default is the whole repository")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--tests", action="store_true", help="include edges that start in a test file, which are left out by default")
    parser.add_argument("--rev", help="read the edges at this commit; default is the working tree")
    parser.add_argument("--base", help="print only the edges added since this commit")
    parser.add_argument("--head", help="with --base: the commit that holds the change; default is the working tree")
    args = parser.parse_args()
    if args.head and not args.base:
        parser.error("--head needs --base")
    if args.rev and args.base:
        parser.error("--rev and --base do not combine")
    keep = lambda pairs: [(source, target) for source, target in pairs if args.tests or not TEST_FILE.search(source)]

    def at(revision):
        """The edges at a commit, or in the working tree with its untracked files when revision is None."""
        if revision:
            files = git(args.repo, "ls-tree", "-r", "--name-only", revision, "--", *args.paths).splitlines()
            return files, keep(edges(at_revision(args.repo, revision, files), files))
        files = git(args.repo, "ls-files", "--", *args.paths).splitlines()
        if args.base:
            files += git(args.repo, "ls-files", "--others", "--exclude-standard", "--", *args.paths).splitlines()
        return files, keep(edges(working_tree(args.repo), files))

    try:
        if args.base:
            _, before = at(args.base)
        files, rows = at(args.head if args.base else args.rev)
    except ValueError as error:
        print(f"import_edges: {error}", file=sys.stderr)
        return 2
    if args.base:
        rows = added(before, rows)
        print(f"# from\tto\twhat the edge changes  (edges added since {args.base}; an absent edge proves nothing)")
        for source, target, notes in rows:
            print(f"{source}\t{target}\t{notes}")
        print(f"import_edges: {len(rows)} added edges, {sum(bool(notes) for _, _, notes in rows)} with a note", file=sys.stderr)
        return 0
    print("# from\tto  (static imports that resolve to a tracked file; an absent edge proves nothing)")
    for source, target in rows:
        print(f"{source}\t{target}")
    print(f"import_edges: {len(rows)} edges from {len(files)} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # the reader, such as `head`, closed the pipe
        sys.exit(0)

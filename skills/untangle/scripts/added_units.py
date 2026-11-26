#!/usr/bin/env python3
"""List the classes and modules a change adds, with what each one holds: leads to surplus.

A unit earns its place by a decision only it makes. For every class or module that is new since
--base, this prints the count of its own methods, how many of those only call another method, its
constants, and what it inherits, extends, or includes. A unit with no method of its own, or with
only methods that call another, is printed as a lead: it may only hold a constant, only delegate,
or only rename another unit. Added units that share a base and have no method of their own are
grouped, because one type for each value of a discriminator is often a list written as types.
A lead is a unit to read, not a finding: a value object, an error class, and a marker type are
correct with no methods. Python is parsed. Ruby is read by indentation, so a file that is not
indented conventionally can be miscounted, and units made by `Class.new` or `Struct.new` are not
seen. Other languages are not covered: read their added types yourself. The change runs from
--base to --head, or to the working tree with its untracked files when --head is not given. Test
files are left out unless --tests is given. Run from the repository root, or pass --repo. Exit 2
for invalid inputs or failed Git operations. No files are written.
"""
import argparse
import ast
from collections import defaultdict
import os
from pathlib import Path
import re
import subprocess
import sys

TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")
RUBY_UNIT = re.compile(r"^(\s*)(module|class)\s+([A-Z][\w:]*)\s*(?:<\s*([\w:.]+(?:\([^)]*\))?))?\s*(?:#.*)?$")
RUBY_DEF = re.compile(r"^(\s*)def\s+(?:self\.)?([\w?!=\[\]<>+\-*/%]+)(.*)$")
RUBY_MIXIN = re.compile(r"^\s*(extend|include|prepend)\s+([A-Z][\w:]*(?:\s*,\s*[A-Z][\w:]*)*)\s*(?:#.*)?$")
RUBY_CONSTANT = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=(?!=)")
RUBY_CALL = re.compile(r"^(?:return\s+)?(?:super\b.*|[A-Za-z_@][\w:@]*(?:(?:\.|&\.)\w+[?!]?)+(?:\(.*\)|\s+\S.*)?|\w+[?!]?\(.*\))$")


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def unit(name, line, bases):
    return {"name": name, "line": line, "bases": list(bases), "methods": 0, "calls": 0, "constants": 0, "nested": 0}


def namespace(one):
    """A unit that holds only other units, as a Ruby file's enclosing modules do: it adds nothing itself."""
    return one["nested"] and not (one["methods"] or one["constants"] or one["bases"])


def only_calls(body):
    """Whether a Python function body, after its docstring, is one statement that calls something."""
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    return len(body) == 1 and isinstance(body[0], (ast.Return, ast.Expr)) and isinstance(body[0].value, ast.Call)


def python_units(text):
    """The classes of a Python file, nested ones under their qualified name."""
    found = []

    def visit(node, prefix):
        for child in node.body:
            if not isinstance(child, ast.ClassDef):
                continue
            one = unit(prefix + child.name, child.lineno, (ast.unparse(base) for base in child.bases))
            for member in child.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    one["methods"] += 1
                    one["calls"] += only_calls(member.body)
                elif isinstance(member, (ast.Assign, ast.AnnAssign)):
                    one["constants"] += 1
                elif isinstance(member, ast.ClassDef):
                    one["nested"] += 1
            found.append(one)
            visit(child, prefix + child.name + ".")

    visit(ast.parse(text), "")
    return found


def ruby_units(text):
    """The modules and classes of a Ruby file, read by indentation: a unit or a method ends at the
    `end` that has the indentation of its first line."""
    found, open_units, method = [], [], None  # method: (indent, unit, body lines) of the def being read
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if method:
            if indent == method[0] and stripped.split("#")[0].strip() == "end":
                method[1]["calls"] += len(method[2]) == 1 and bool(RUBY_CALL.match(method[2][0]))
                method = None
            else:
                method[2].append(stripped.split(" #")[0].strip())
            continue
        if open_units and indent == open_units[-1][0] and stripped.split("#")[0].strip() == "end":
            open_units.pop()
            continue
        start = RUBY_UNIT.match(line)
        if start:
            prefix = open_units[-1][1]["name"] if open_units else ""
            name = f"{prefix}::{start.group(3)}" if prefix else start.group(3)
            one = unit(name, number, [start.group(4)] if start.group(4) else [])
            if open_units:
                open_units[-1][1]["nested"] += 1
            found.append(one)
            open_units.append((indent, one))
            continue
        if not open_units:
            continue
        owner = open_units[-1][1]
        define = RUBY_DEF.match(line)
        if define:
            owner["methods"] += 1
            rest = define.group(3).strip()
            endless = re.match(r"^(?:\([^)]*\))?\s*=\s*(.+)$", rest)
            if endless:  # def name(args) = expression
                owner["calls"] += bool(RUBY_CALL.match(endless.group(1).split(" #")[0].strip()))
            elif not re.search(r";\s*end\s*$", rest):
                method = (len(define.group(1)), owner, [])
            continue
        mixin = RUBY_MIXIN.match(line)
        if mixin:
            owner["bases"] += [f"{mixin.group(1)} {name.strip()}" for name in mixin.group(2).split(",")]
        elif RUBY_CONSTANT.match(line):
            owner["constants"] += 1
    return found


PARSERS = {".py": python_units, ".rb": ruby_units}


def parse(path, text):
    try:
        return PARSERS[Path(path).suffix](text)
    except (SyntaxError, ValueError):
        return None


def describe(one):
    methods = f"{one['methods']} method{'' if one['methods'] == 1 else 's'}"
    if one["calls"]:
        methods += f" ({one['calls']} only call{'s' if one['calls'] == 1 else ''} another)"
    constants = f"{one['constants']} constant{'' if one['constants'] == 1 else 's'}"
    return f"{methods}, {constants}" + (f"; {', '.join(one['bases'])}" if one["bases"] else "")


def base_name(base):
    return re.sub(r"^(?:extend|include|prepend)\s+", "", base)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="limit to these paths; default is the whole repository")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base", required=True, help="the commit the change starts from")
    parser.add_argument("--head", help="the commit that holds the change; default is the working tree")
    parser.add_argument("--tests", action="store_true", help="include test files, which are left out by default")
    args = parser.parse_args()
    repo = Path(args.repo)
    try:
        revisions = [args.base, args.head] if args.head else [args.base]
        status = [line.split("\t", 1) for line in git(repo, "diff", "--name-status", "--no-renames", *revisions, "--", *args.paths).splitlines()]
        if not args.head:  # a file Git does not track yet is added as a whole
            status += [["A", path] for path in git(repo, "ls-files", "--others", "--exclude-standard", "--", *args.paths).splitlines()]
        at_base = set(git(repo, "ls-tree", "-r", "--name-only", args.base).splitlines())
    except ValueError as error:
        print(f"added_units: {error}", file=sys.stderr)
        return 2
    status = [(state, path) for state, path in status if Path(path).suffix in PARSERS and (args.tests or not TEST_FILE.search(path))]
    before, unparsed = {}, []  # path -> the units the base holds there
    for state, path in status:
        if path in at_base:
            before[path] = parse(path, git(repo, "show", f"{args.base}:{path}")) or []
    known = defaultdict(list)  # unit name -> the changed files that hold it at the base
    for path, units in before.items():
        for one in units:
            known[one["name"]].append(path)
    rows = []
    for state, path in status:
        if state == "D":
            continue
        try:
            text = git(repo, "show", f"{args.head}:{path}") if args.head else (repo / path).read_text(errors="replace")
        except (ValueError, OSError):
            continue
        units = parse(path, text)
        if units is None:
            unparsed.append(path)
            continue
        old = {one["name"] for one in before.get(path, [])}
        for one in units:
            if one["name"] in old or namespace(one):
                continue
            elsewhere = [other for other in known[one["name"]] if other != path]
            rows.append((path, one, elsewhere))
    leads = [(path, one, elsewhere) for path, one, elsewhere in rows if one["methods"] == one["calls"]]
    files = len({path for path, _, _ in rows})
    target = f"{args.base} to {args.head}" if args.head else f"{args.base} to the working tree"
    print(f"Units added from {target}: {len(rows)} in {files} files; {len(leads)} are leads "
          "(no method of their own, or only methods that call another).")
    groups = defaultdict(list)
    for path, one, _ in leads:
        if not one["methods"]:
            for base in one["bases"]:
                groups[base_name(base)].append(one["name"])
    groups = {base: names for base, names in groups.items() if len(names) > 1}
    if groups:
        print("\n## Added units of one base with no method of their own\n")
        for base, names in sorted(groups.items()):
            print(f"{base}: {', '.join(names)}")
    for title, chosen in (("Leads", leads), ("Other added units", [row for row in rows if row not in leads])):
        if chosen:
            print(f"\n## {title}\n")
            for path, one, elsewhere in chosen:
                moved = f"\tthe base holds a unit of this name in {', '.join(sorted(set(elsewhere)))}" if elsewhere else ""
                print(f"{path}:{one['line']}\t{one['name']}\t{describe(one)}{moved}")
    if unparsed:
        print(f"\nNot parsed: {', '.join(unparsed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

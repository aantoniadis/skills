#!/usr/bin/env python3
"""List what a change adds that may decide nothing of its own: leads to surplus.

A unit earns its place by a decision only it makes. For the change from --base, this prints:

- each class or module that is new, with the count of its own methods, how many of those only
  call another method, its constants, and what it inherits, extends, or includes; and each new
  file that defines no class or module, with its functions and constants. One with no method
  or function of its own, or with only ones that call another, is a lead: it may only hold a
  constant, only delegate, or only rename another unit;
- added units that share a base, and added files of one directory, that hold only constants,
  grouped: one type or file for each value of a discriminator is often a list written as types;
- each added function or method that only passes its own parameters on to one call: a
  possible wrapper. One with no parameter is not listed;
- each added parameter with a default that no line outside its definition sets by keyword;
- each added unit that exactly one other unit inherits, extends, or includes;
- each added unit that takes the short name of a unit defined elsewhere: inside its namespace
  the name now means the new unit.

A lead is a place to read, not a finding: a value object, an error class, and a marker type are
correct with no methods. The script does not look for types in other languages, units made at
run time (`Class.new`, `Struct.new`, `type()`), an option that callers set by position, a
wrapper with no parameter, or a method that calls another and also decides something, so
"0 leads" clears nothing: read the diff for those. Python is parsed. Ruby is read by indentation, so a file that is not indented
conventionally can be miscounted. The change runs from --base to --head, or to the working
tree with its untracked files when --head is not given. Test files are left out unless --tests
is given. Run from the repository root, or pass --repo. Exit 2 for invalid inputs or failed
Git operations. No files are written.
"""
import argparse
import ast
from collections import defaultdict
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]+$|[._-](test|spec)\.\w+$|Tests?\.\w+$")
RUBY_UNIT = re.compile(r"^(\s*)(module|class)\s+([A-Z][\w:]*)\s*(?:<\s*([\w:.]+(?:\([^)]*\))?))?\s*(?:#.*)?$")
RUBY_DEF = re.compile(r"^(\s*)def\s+(?:self\.)?([\w?!=\[\]<>+\-*/%]+)(.*)$")
RUBY_MIXIN = re.compile(r"^\s*(extend|include|prepend)\s+([A-Z][\w:]*(?:\s*,\s*[A-Z][\w:]*)*)\s*(?:#.*)?$")
RUBY_CONSTANT = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=(?!=)")
RUBY_CALL = re.compile(r"^(?:return\s+)?((?:[A-Za-z_@][\w:@]*(?:\.|&\.))*)\w+[?!]?(?:\(([^()]*)\))?$")
RUBY_PARAMETER = re.compile(r"^\s*(?:\*{1,2}|&)?(\w+)\s*(:\s*\S|=\s*\S)?")
NOT_LOOKED_FOR = ("Not looked for: types in other languages, units made at run time, an option set by position, a wrapper with no "
                  "parameter, and a method that calls another and also decides something. Read the diff for those; no lead here clears them.")


def git(repo, *args, ok=(0,)):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], env=env, capture_output=True, text=True)
    if result.returncode not in ok:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def unit(name, line, bases):
    return {"name": name, "line": line, "bases": list(bases), "methods": 0, "calls": 0, "constants": 0, "nested": 0}


def function(name, line, calls, options):
    """options: (parameter name, the line that declares it) for each parameter with a default."""
    return {"name": name, "line": line, "calls": bool(calls), "options": list(options)}


def namespace(one):
    """A unit that holds only other units, as a Ruby file's enclosing modules do: it adds nothing itself."""
    return one["nested"] and not (one["methods"] or one["constants"] or one["bases"])


def only_calls(node):
    """Whether a Python function, after its docstring, is one call that passes on exactly its own parameters."""
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not (len(body) == 1 and isinstance(body[0], (ast.Return, ast.Expr)) and isinstance(body[0].value, ast.Call)):
        return False
    call, arguments = body[0].value, node.args
    own = {arg.arg for arg in arguments.posonlyargs + arguments.args + arguments.kwonlyargs} - {"self", "cls"}
    passed = [arg.value if isinstance(arg, ast.Starred) else arg for arg in call.args] + [keyword.value for keyword in call.keywords]
    used = {name.id for name in ast.walk(call) if isinstance(name, ast.Name)}
    return bool(own) and all(isinstance(arg, ast.Name) for arg in passed) and own <= used


def python_options(node):
    arguments = node.args
    positional = arguments.posonlyargs + arguments.args
    with_default = positional[len(positional) - len(arguments.defaults):] if arguments.defaults else []
    with_default += [arg for arg, default in zip(arguments.kwonlyargs, arguments.kw_defaults) if default is not None]
    return [(arg.arg, arg.lineno) for arg in with_default]


def python_file(text):
    """The classes and functions of a Python file, nested ones under their qualified name, and its top-level constants."""
    units, functions, constants = [], [], 0
    tree = ast.parse(text)

    def visit(node, prefix, owner):
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(function(prefix + child.name, child.lineno, only_calls(child), python_options(child)))
                if owner:
                    owner["methods"] += 1
                    owner["calls"] += only_calls(child)
            elif isinstance(child, ast.ClassDef):
                one = unit(prefix + child.name, child.lineno, (ast.unparse(base) for base in child.bases))
                if owner:
                    owner["nested"] += 1
                units.append(one)
                visit(child, prefix + child.name + ".", one)
            elif isinstance(child, (ast.Assign, ast.AnnAssign)) and owner:
                owner["constants"] += 1

    visit(tree, "", None)
    constants = sum(isinstance(child, (ast.Assign, ast.AnnAssign)) for child in tree.body)
    return {"units": units, "functions": functions, "constants": constants}


def ruby_parameters(signature):
    """(name, whether it has a default) for each parameter of a parenthesized Ruby signature."""
    inside = re.match(r"^\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", signature)
    found = []
    for part in re.split(r",(?![^(\[{]*[)\]}])", inside.group(1)) if inside else []:
        parameter = RUBY_PARAMETER.match(part)
        if parameter:
            found.append((parameter.group(1), bool(parameter.group(2)) and not part.strip().endswith(":")))
    return found


def ruby_only_calls(line, parameters):
    """Whether a one-line Ruby body is one call that passes on exactly the method's own parameters."""
    call, own = RUBY_CALL.match(line), {name for name, _ in parameters}
    if not (call and own):
        return False
    passed = [re.sub(r"^(?:\*{1,2}|&|\w+:\s*)", "", part.strip()) for part in (call.group(2) or "").split(",") if part.strip()]
    receiver = re.split(r"\.|&\.", call.group(1))[0]
    return all(re.fullmatch(r"\w+", part) for part in passed) and own <= set(passed) | {receiver}


def ruby_file(text):
    """The modules, classes, and methods of a Ruby file, read by indentation: a unit or a method
    ends at the `end` that has the indentation of its first line."""
    units, functions, constants, open_units, method = [], [], 0, [], None  # method: (indent, function, body lines)
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if method:
            if indent == method[0] and stripped.split("#")[0].strip() == "end":
                method[1]["calls"] = len(method[2]) == 1 and ruby_only_calls(method[2][0], method[3])
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
            one = unit(f"{prefix}::{start.group(3)}" if prefix else start.group(3), number, [start.group(4)] if start.group(4) else [])
            if open_units:
                open_units[-1][1]["nested"] += 1
            units.append(one)
            open_units.append((indent, one))
            continue
        owner = open_units[-1][1] if open_units else None
        define = RUBY_DEF.match(line)
        if define:
            rest = define.group(3).strip()
            parameters = ruby_parameters(rest)
            one = function(f"{owner['name']}.{define.group(2)}" if owner else define.group(2), number, False,
                           [(name, number) for name, default in parameters if default])
            functions.append(one)
            endless = re.match(r"^(?:\([^()]*(?:\([^()]*\)[^()]*)*\))?\s*=\s*(.+)$", rest)
            if endless:  # def name(args) = expression
                one["calls"] = ruby_only_calls(endless.group(1).split(" #")[0].strip(), parameters)
            elif not re.search(r";\s*end\s*$", rest):
                method = (len(define.group(1)), one, [], parameters)
            continue
        mixin = RUBY_MIXIN.match(line)
        if mixin and owner:
            owner["bases"] += [f"{mixin.group(1)} {name.strip()}" for name in mixin.group(2).split(",")]
        elif RUBY_CONSTANT.match(line):
            if owner:
                owner["constants"] += 1
            else:
                constants += 1
    for one in units:  # a method's count belongs to the unit that holds it
        own = [f for f in functions if f["name"].rpartition(".")[0] == one["name"]]
        one["methods"], one["calls"] = len(own), sum(f["calls"] for f in own)
    return {"units": units, "functions": functions, "constants": constants}


PARSERS = {".py": python_file, ".rb": ruby_file}
SETS_BY_KEYWORD = {".py": r"\bNAME=[^=]", ".rb": r"\bNAME:\s"}
DEFINES = {".py": r"^\s*class\s+NAME\b", ".rb": r"^\s*(?:class|module)\s+(?:[A-Z]\w*::)*NAME\b"}
EXTENDS = {".py": r"^\s*class\s+\w+\s*\([^)]*\bNAME\b", ".rb": r"(?:<\s*(?:[A-Z]\w*::)*NAME\b|\b(?:extend|include|prepend)\s+(?:[A-Z]\w*::)*NAME\b)"}


def parse(path, text):
    try:
        return PARSERS[Path(path).suffix](text)
    except (SyntaxError, ValueError):
        return None


def describe(one, word="method"):
    methods = f"{one['methods']} {word}{'' if one['methods'] == 1 else 's'}"
    if one["calls"]:
        methods += f" ({one['calls']} only pass{'es' if one['calls'] == 1 else ''} parameters on)"
    constants = f"{one['constants']} constant{'' if one['constants'] == 1 else 's'}"
    return f"{methods}, {constants}" + (f"; {', '.join(one['bases'])}" if one.get("bases") else "")


def short(name):
    return re.split(r"::|\.", re.sub(r"^(?:extend|include|prepend)\s+", "", name))[-1]


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
    wanted = lambda path: Path(path).suffix in PARSERS and (args.tests or not TEST_FILE.search(path))
    status = [(state, path) for state, path in status if wanted(path)]

    def search(name, pattern, suffix):
        """(path, line number) of each source line at the head where the pattern, with the name in it, matches.
        Git finds the lines that hold the name as a word; the pattern is applied here. Test files are left out unless asked."""
        where = [args.head] if args.head else ["--untracked"]
        out = git(repo, "grep", "-n", "-I", "-F", "-w", "-e", name, *where, "--", f"*{suffix}", ok=(0, 1))
        wanted_line, hits = re.compile(pattern.replace("NAME", re.escape(name))), []
        for line in out.splitlines():
            parts = line.split(":", 3 if args.head else 2)
            if len(parts) < 3:
                continue
            path, number, text = parts[-3], parts[-2], parts[-1]
            if wanted(path) and number.isdigit() and wanted_line.search(text):
                hits.append((path, int(number)))
        return hits

    before, unparsed = {}, []  # path -> what the base holds there
    for state, path in status:
        if path in at_base:
            before[path] = parse(path, git(repo, "show", f"{args.base}:{path}")) or {"units": [], "functions": [], "constants": 0}
    known = defaultdict(list)  # unit name -> the changed files that hold it at the base
    for path, parsed in before.items():
        for one in parsed["units"]:
            known[one["name"]].append(path)
    units, files, wrappers, options = [], [], [], []
    for state, path in status:
        if state == "D":
            continue
        try:
            text = git(repo, "show", f"{args.head}:{path}") if args.head else (repo / path).read_text(errors="replace")
        except (ValueError, OSError):
            continue
        parsed = parse(path, text)
        if parsed is None:
            unparsed.append(path)
            continue
        old = before.get(path, {"units": [], "functions": []})
        old_units = {one["name"] for one in old["units"]}
        old_functions = {one["name"]: one for one in old["functions"]}
        added_here = [one for one in parsed["units"] if one["name"] not in old_units and not namespace(one)]
        for one in added_here:
            units.append((path, one, [other for other in known[one["name"]] if other != path]))
        top = [f for f in parsed["functions"] if not any(f["name"].startswith(u["name"] + ".") for u in parsed["units"])]
        if path not in at_base and not [u for u in parsed["units"] if not namespace(u)] and (top or parsed["constants"]):
            files.append((path, {"name": path, "line": 1, "methods": len(top), "calls": sum(f["calls"] for f in top), "constants": parsed["constants"]}))
        for one in parsed["functions"]:
            was = old_functions.get(one["name"])
            if was is None and one["calls"]:
                wrappers.append((path, one))
            had = {name for name, _ in was["options"]} if was else set()
            options += [(path, one, name, line) for name, line in one["options"] if name not in had]

    unset = []
    for path, one, name, line in options:
        suffix = Path(path).suffix
        if not [hit for hit in search(name, SETS_BY_KEYWORD[suffix], suffix) if hit != (path, line)]:
            unset.append((path, one, name, line))
    single = []
    for path, one, _ in units:
        suffix = Path(path).suffix
        users = [hit for hit in search(short(one["name"]), EXTENDS[suffix], suffix) if hit != (path, one["line"])]
        if len(users) == 1:
            single.append((path, one, users[0]))

    def text_at_head(path):
        try:
            return git(repo, "show", f"{args.head}:{path}") if args.head else (repo / path).read_text(errors="replace")
        except (ValueError, OSError):
            return ""

    same_name = []
    for path, one, _ in units:
        suffix, name = Path(path).suffix, short(one["name"])
        for other_path in sorted({hit[0] for hit in search(name, DEFINES[suffix], suffix)}):
            others = [other for other in (parse(other_path, text_at_head(other_path)) or {"units": []})["units"]
                      if short(other["name"]) == name and other["name"] != one["name"]]
            same_name += [(path, one, other_path, other) for other in others]

    hollow = [(path, one, elsewhere) for path, one, elsewhere in units if one["methods"] == one["calls"]]
    hollow_files = [(path, one) for path, one in files if one["methods"] == one["calls"]]
    by_base, by_directory = defaultdict(list), defaultdict(list)
    for path, one, _ in hollow:
        if not one["methods"]:
            for base in one["bases"]:
                by_base[re.sub(r"^(?:extend|include|prepend)\s+", "", base)].append(one["name"])
    for path, one in hollow_files:
        if not one["methods"]:
            by_directory[str(PurePosixPath(path).parent)].append(PurePosixPath(path).name)
    by_base = {key: names for key, names in by_base.items() if len(names) > 1}
    by_directory = {key: names for key, names in by_directory.items() if len(names) > 1}
    leads = len(hollow) + len(hollow_files) + len(wrappers) + len(unset) + len(single) + len(same_name)
    target = f"{args.base} to {args.head}" if args.head else f"{args.base} to the working tree"
    print(f"Leads from {target}: {leads}. The change adds {len(units)} classes or modules, {len(files)} files with no class "
          f"or module, {len(options)} options with a default, and {len(wrappers)} functions that only pass their parameters on.")

    def section(title, lines):
        if lines:
            print(f"\n## {title}\n")
            print("\n".join(lines))

    section("Added units of one base with no method of their own", [f"{base}: {', '.join(names)}" for base, names in sorted(by_base.items())])
    section("Added files of one directory that hold only constants", [f"{directory}/: {', '.join(names)}" for directory, names in sorted(by_directory.items())])
    moved = lambda elsewhere: f"\tthe base holds a unit of this name in {', '.join(sorted(set(elsewhere)))}" if elsewhere else ""
    section("Added units and files with no method or function of their own",
            [f"{path}:{one['line']}\t{one['name']}\t{describe(one)}{moved(elsewhere)}" for path, one, elsewhere in hollow]
            + [f"{path}\t(file)\t{describe(one, 'function')}" for path, one in hollow_files])
    section("Added functions that only pass their parameters on to one call", [f"{path}:{one['line']}\t{one['name']}" for path, one in wrappers])
    section("Added options that nothing sets by keyword", [f"{path}:{line}\t{one['name']}\t{name}" for path, one, name, line in unset])
    section("Added units that one unit extends", [f"{path}:{one['line']}\t{one['name']}\textended only at {user[0]}:{user[1]}" for path, one, user in single])
    section("Added units that take the name of another unit",
            [f"{path}:{one['line']}\t{one['name']}\t{other_path}:{other['line']} defines {other['name']}" for path, one, other_path, other in same_name])
    section("Other added units", [f"{path}:{one['line']}\t{one['name']}\t{describe(one)}{moved(elsewhere)}"
                                  for path, one, elsewhere in units if (path, one, elsewhere) not in hollow]
            + [f"{path}\t(file)\t{describe(one, 'function')}" for path, one in files if (path, one) not in hollow_files])
    if unparsed:
        print(f"\nNot parsed: {', '.join(unparsed)}")
    print(f"\n{NOT_LOOKED_FOR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

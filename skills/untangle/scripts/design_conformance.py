#!/usr/bin/env python3
"""Compare a stated design with the dependencies the code has.

The stated design is a JSON file: named components, each a list of path patterns, and the
dependencies allowed between them.

    {"components": {"api": ["app/api/**"], "domain": ["app/domain/**"], "storage": ["app/db/**"]},
     "allowed": [["api", "domain"], ["domain", "storage"]]}

The dependencies are a TSV of `from<TAB>to` file paths, such as import_edges.py or a
dependency tool writes. Every relationship gets one result: *as stated* (allowed and present),
*not stated* (present, and the design does not allow it), or *not found* (allowed, and no
edge shows it). A result is only as complete as the edges: a missing edge can mean a
dependency the tool cannot see. A file matches the first component whose pattern fits it.
Exit 2 for invalid inputs. No files are written.
"""
import argparse
from collections import defaultdict
import json
import re
import sys


def pattern_regex(pattern):
    """A path pattern as a regular expression: `**` crosses directories, `*` and `?` stay inside one."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def load_design(path):
    with open(path, encoding="utf-8") as handle:
        design = json.load(handle)
    components = design.get("components")
    if not isinstance(components, dict) or not components:
        raise ValueError("the design needs a non-empty \"components\" object of name -> path patterns")
    allowed = {tuple(pair) for pair in design.get("allowed", [])}
    for pair in allowed:
        if len(pair) != 2 or any(name not in components for name in pair):
            raise ValueError(f"\"allowed\" names an unknown component or is not a pair: {list(pair)}")
    return {name: [pattern_regex(p) for p in patterns] for name, patterns in components.items()}, allowed


def component_of(path, components):
    return next((name for name, patterns in components.items() if any(p.match(path) for p in patterns)), None)


def read_edges(path):
    edges = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and not line.startswith("#"):
                edges.append((parts[0], parts[1]))
    return edges


def compare(components, allowed, edges):
    """(results, unmapped): results maps (from, to) -> (result, [file edges]); unmapped lists
    files with an edge and no component."""
    present, unmapped = defaultdict(list), set()
    for source, target in edges:
        a, b = component_of(source, components), component_of(target, components)
        unmapped.update(path for path, name in ((source, a), (target, b)) if name is None)
        if a and b and a != b:
            present[(a, b)].append((source, target))
    results = {}
    for pair in sorted(set(present) | allowed):
        result = ("as stated" if pair in allowed else "not stated") if pair in present else "not found"
        results[pair] = (result, sorted(present.get(pair, [])))
    return results, sorted(unmapped)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("design", help="JSON file with the stated components and allowed dependencies")
    parser.add_argument("edges", help="TSV of from<TAB>to file paths")
    parser.add_argument("--show", type=int, default=5, help="file edges to print under each relationship")
    args = parser.parse_args()
    try:
        components, allowed = load_design(args.design)
        edges = read_edges(args.edges)
    except (OSError, ValueError) as error:
        print(f"design_conformance: {error}", file=sys.stderr)
        return 2
    results, unmapped = compare(components, allowed, edges)
    counts = {label: sum(1 for result, _ in results.values() if result == label) for label in ("as stated", "not stated", "not found")}
    print(f"Relationships: {counts['as stated']} as stated, {counts['not stated']} not stated, {counts['not found']} not found "
          f"(from {len(edges)} file edges).\n")
    print("from\tto\tresult\tfile edges")
    for (source, target), (result, files) in sorted(results.items(), key=lambda item: (item[1][0] != "not stated", item[0])):
        print(f"{source}\t{target}\t{result}\t{len(files)}")
        for a, b in files[:args.show]:
            print(f"\t\t\t{a} -> {b}")
        if len(files) > args.show:
            print(f"\t\t\t... {len(files) - args.show} more")
    if unmapped:
        print(f"\nFiles with an edge and no component ({len(unmapped)}); add them to the design or state why they are outside it:")
        for path in unmapped[:40]:
            print(f"  {path}")
        if len(unmapped) > 40:
            print(f"  ... {len(unmapped) - 40} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())

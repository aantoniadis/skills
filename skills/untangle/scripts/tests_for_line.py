#!/usr/bin/env python3
"""List the tests that execute a source line, from coverage.py data recorded per test.

Record the data with a context per test, for example `pytest --cov=<package> --cov-context=test`
or `dynamic_context = test_function` in the coverage configuration. Then:

    tests_for_line.py .coverage pricing/discounts.py:12 api/serializers.py:44

A path matches by suffix. A line no test executes prints 0 tests: it is untested, which is
not the same as unreachable. For another ecosystem, use its own per-test coverage report.
Reads the SQLite file directly; needs no package. Exit 2 for invalid inputs. No files are
written.
"""
import argparse
import sqlite3
import sys


def lines_of(numbits):
    """The line numbers in a coverage.py numbits blob: bit n of the blob is line n."""
    return {index * 8 + bit for index, byte in enumerate(numbits) for bit in range(8) if byte & (1 << bit)}


def tests_for(database, suffix, line):
    """Sorted test contexts that executed the line of the file whose path ends with suffix."""
    tests = set()
    rows = database.execute("select c.context, l.numbits from line_bits l join file f on f.id = l.file_id "
                            "join context c on c.id = l.context_id where f.path like ?", ("%" + suffix,))
    tests.update(context for context, numbits in rows if context and line in lines_of(numbits))
    # Data recorded with branch coverage keeps arcs in place of lines.
    rows = database.execute("select distinct c.context from arc a join file f on f.id = a.file_id join context c on c.id = a.context_id "
                            "where f.path like ? and (a.fromno = ? or a.tono = ?)", ("%" + suffix, line, line))
    tests.update(context for (context,) in rows if context)
    return sorted(tests)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("coverage", help="the coverage.py data file, usually .coverage")
    parser.add_argument("lines", nargs="+", help="<path suffix>:<line>")
    parser.add_argument("--show", type=int, default=5, help="tests to print per line")
    args = parser.parse_args()
    try:
        database = sqlite3.connect(f"file:{args.coverage}?mode=ro", uri=True)
        contexts = database.execute("select count(*) from context where context != ''").fetchone()[0]
        specs = [(spec.rsplit(":", 1)[0], int(spec.rsplit(":", 1)[1])) for spec in args.lines]
        results = [(suffix, line, tests_for(database, suffix, line)) for suffix, line in specs]
    except (sqlite3.Error, ValueError, IndexError) as error:
        print(f"tests_for_line: {error}", file=sys.stderr)
        return 2
    if not contexts:
        print("tests_for_line: this data has no per-test contexts; record it again with a context per test", file=sys.stderr)
        return 2
    for suffix, line, tests in results:
        print(f"{suffix}:{line}\t{len(tests)} tests")
        for test in tests[:args.show]:
            print(f"\t{test}")
        if len(tests) > args.show:
            print(f"\t... {len(tests) - args.show} more")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # the reader, such as `head`, closed the pipe
        sys.exit(0)

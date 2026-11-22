#!/usr/bin/env python3
"""Check a thorough search's candidate table and estimate how much the finders left.

The table is Markdown at the investigation location, one row for each candidate a
finder returned:

  | Candidate | Finders | Disposition |
  |---|---|---|
  | release() blocks a waiting acquire | 1, 3 | delivered |
  | same, through release(force=True) | 2 | merged into release() blocks a waiting acquire |
  | lifetime warning text | 4 | dropped: base prints the same text, probe p3 |

A disposition is `delivered`, `merged into <candidate>`, or `dropped: <counterevidence>`.
List a merged row's finders on the row it merged into as well.

The estimate uses the delivered rows: how many finders returned each one. Many
candidates seen by one finder only mean that more finders would find more. It is the
bias-corrected Chao2 estimator for incidence data, and with a handful of finders it
is rough. It counts what reads of this kind find, never defects none of them reach.

  remaining.py --finders <number of finders started> <candidates.md>

Exit 0 when every row has a disposition, 1 when a row lacks one, 2 for invalid input.
No files are written.
"""
import argparse
from pathlib import Path
import re
import sys

DISPOSITION = re.compile(r"^(delivered\b|merged into \S|dropped: \S)", re.I)


def rows(text):
    header, found = None, []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")] if line.strip().startswith("|") else None
        if not cells:
            continue
        if header is None:
            header = [cell.lower() for cell in cells]
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        found.append(dict(zip(header, cells)))
    if header is None or not {"candidate", "finders", "disposition"} <= set(header):
        raise ValueError("no table with Candidate, Finders, and Disposition columns")
    return found


def estimate(finder_sets, finders):
    seen = len(finder_sets)
    once = sum(1 for ids in finder_sets if len(ids) == 1)
    twice = sum(1 for ids in finder_sets if len(ids) == 2)
    return seen, once, twice, seen + (finders - 1) / finders * once * (once - 1) / (2 * (twice + 1))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--finders", type=int, required=True, help="number of finders started")
    parser.add_argument("table")
    args = parser.parse_args(argv)
    if args.finders < 2:
        parser.exit(2, "--finders must be at least 2\n")
    try:
        table = rows(Path(args.table).read_text())
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    undecided = [row["candidate"] for row in table if not DISPOSITION.match(row.get("disposition", ""))]
    delivered = [row for row in table if row.get("disposition", "").lower().startswith("delivered")]
    sets = [set(re.findall(r"[\w-]+", row["finders"])) for row in delivered]
    if undecided:
        print(f"{len(undecided)} candidates without a disposition:")
        print("\n".join(f"- {name}" for name in undecided))
        return 1
    if not delivered:
        print(f"{len(table)} candidates, none delivered: no estimate.")
        return 0
    seen, once, twice, total = estimate(sets, args.finders)
    print(f"{len(table)} candidates: {seen} delivered, {len(table) - seen} merged or dropped.")
    print(f"Delivered candidates found by one finder: {once}; by two: {twice}.")
    print(f"Estimated total that reads of this kind find: about {total:.0f}; "
          f"this search found about {100 * seen / total:.0f}% of it. Rough with {args.finders} finders.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

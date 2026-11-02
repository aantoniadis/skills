#!/usr/bin/env python3
"""Size each skill's reading set: SKILL.md, the files it links (one hop), and their links (two hops).

  python3 evals/reading_set.py [<checkout>]

Words and a token estimate (characters / 4) per skill; a shared-file table below. Markdown links to
.md files only; the two-hop set is the ceiling an invocation can load, not what every run reads.
"""
import re
import sys
from pathlib import Path

LINK = re.compile(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")


def links(path):
    return [target for target in ((path.parent / t).resolve() for t in LINK.findall(path.read_text()))
            if target.is_file()]


def reach(start, hops):
    seen, frontier = {start}, [start]
    for _ in range(hops):
        frontier = [t for p in frontier for t in links(p) if t not in seen and not seen.add(t)]
    return seen


def main(root):
    skills = root / "skills"
    print(f"{'skill':18}{'own':>6}{'files':>6}{'1 hop':>7}{'~tok':>7}{'files':>6}{'2 hops':>7}{'~tok':>7}")
    for skill in sorted(skills.glob("*/SKILL.md")):
        one, two = reach(skill, 1), reach(skill, 2)
        counts = [len(skill.read_text().split())]
        for group in (one, two):
            text = "".join(p.read_text() for p in group)
            counts += [len(group), len(text.split()), len(text) // 4]
        print(f"{skill.parent.name:18}{counts[0]:6}{counts[1]:6}{counts[2]:7}{counts[3]:7}{counts[4]:6}{counts[5]:7}{counts[6]:7}")
    print("\nshared files, words:")
    for path in sorted(skills.glob("*.md"), key=lambda p: -len(p.read_text().split())):
        print(f"  {path.name:26}{len(path.read_text().split()):6}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())

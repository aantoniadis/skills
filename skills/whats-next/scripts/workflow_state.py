#!/usr/bin/env python3
"""Print a project's workflow state for whats-next: the Git position, the notes and reports
our skills already wrote (by the `kind:` in their front matter, else by their template's marker
line), and the workflow markers in the checkout. Read-only; creates nothing."""

import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from investigation_dir import RECORD  # noqa: E402
from tool_setup_path import INSTRUCTIONS, git, git_root, project_root, record_path  # noqa: E402

# (front-matter kind, printed kind, owning skill, the marker line the template carried before `kind:` existed)
KINDS = (
    ("understanding-note", "understanding note", "explain", r"^\*\*Answer:\*\*"),
    ("plan", "plan", "plan-change", r"^## Delivery slices$"),
    ("diagnosis-note", "diagnosis note", "fix-bug", r"^\*\*Checked:\*\*"),
    ("pr-review-guide", "PR review guide", "pr-review-guide", r"^## What the change does$"),
    ("acceptance-report", "acceptance report", "check-acceptance", r"^## What was asked$"),
)
KIND_LINE = re.compile(r"\A---\n(?:(?!---\n)[^\n]*\n)*?kind:\s*([\w-]+)\s*\n(?:(?!---\n)[^\n]*\n)*?---\n")
SUMMARY = re.compile(r"^\*\*(?:Readiness|Bottom line|Verdict|Answer):\*\*\s*(.+)", re.M)
SKIP = {".git", "node_modules", ".venv", "venv", "dist", "build"}
CAP = 400  # Markdown files read before the scan stops and says so.


def classify(text):
    declared = KIND_LINE.match(text)
    for slug, kind, skill, marker in KINDS:
        if declared and declared.group(1) == slug:
            return kind, skill
    for slug, kind, skill, marker in KINDS:
        if not declared and re.search(marker, text, re.M):
            return kind, skill
    return None


def investigation_base(root):
    for name in INSTRUCTIONS:
        path = root / name
        match = RECORD.search(path.read_text(errors="replace")) if path.is_file() else None
        if match:
            return (root / (match.group(1) or match.group(2))).resolve(), "recorded"
    return root / ".scratch", "default"


def artifacts(root, bases):
    found, seen, read = {}, set(), 0
    for base in bases:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            # A recorded location can sit outside the checkout; skip-list on the parts under its base then.
            parts = path.relative_to(root if path.is_relative_to(root) else base).parts
            if path in seen or SKIP & set(parts):
                continue
            seen.add(path)
            read += 1
            if read > CAP:
                return list(found.values()), True
            text = path.read_text(errors="replace")
            kind = classify(text)
            if kind:
                summary = SUMMARY.search(text)
                found[path] = (path.stat().st_mtime, path, *kind, summary.group(1)[:160] if summary else "")
    return list(found.values()), False


def git_state(root):
    def out(*args):
        result = git(root, *args)
        return result.stdout.strip() if result.returncode == 0 else None

    branch = out("rev-parse", "--abbrev-ref", "HEAD")
    default = (out("symbolic-ref", "--short", "refs/remotes/origin/HEAD") or "").removeprefix("origin/")
    if not default:
        default = next((name for name in ("main", "master") if out("rev-parse", "--verify", "-q", f"refs/heads/{name}")), None)
    upstream = out("rev-parse", "--abbrev-ref", "@{upstream}")
    dirty = sum(1 for line in (out("status", "--porcelain") or "").splitlines() if line)
    distance = ""
    if default and branch != default:
        counts = out("rev-list", "--left-right", "--count", f"{default}...HEAD")
        if counts:
            behind, ahead = counts.split()
            distance = f" · ahead of {default} by {ahead}, behind by {behind}"
    elif default:
        distance = f" · on the default branch"
    return (f"- Branch: `{branch}` (upstream: {upstream or 'none'}){distance} · "
            f"{dirty} uncommitted file{'s' if dirty != 1 else ''} · last commit: {out('log', '-1', '--format=%h %s') or 'none'}")


def markers(root):
    scratch = root / ".scratch"
    tickets = sorted(p for p in scratch.glob("*/issues") if p.is_dir()) if scratch.is_dir() else []
    record = record_path(root)
    return [
        ("Matt's tracker setup (`docs/agents/issue-tracker.md`)", (root / "docs/agents/issue-tracker.md").is_file()),
        ("Glossary (`GLOSSARY.md`)", (root / "GLOSSARY.md").is_file()),
        ("Local tickets" + (f" ({', '.join(str(p.relative_to(root)) for p in tickets)})" if tickets else " (`.scratch/<feature>/issues/`)"), bool(tickets)),
        ("`visual-pr` tasks (`.humanlayer/tasks/`)", (root / ".humanlayer/tasks").is_dir()),
        (f"Local tool record (`{record}`)", record.is_file()),
    ]


def report(project):
    root = project_root(project)
    lines = [f"# Workflow state: {root}", ""]
    lines.append(git_state(root) if git_root(root) else "- Not a Git checkout")
    base, origin = investigation_base(root)
    lines.append(f"- Investigation location: `{base}` ({origin})")
    lines += ["", "## Notes and reports, newest first"]
    found, capped = artifacts(root, [base, root / ".scratch", root / "docs"])
    for _, path, kind, skill, summary in sorted(found, key=lambda item: item[0], reverse=True):
        day = datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        lines.append(f"- {kind} ({skill}): `{rel}` · {day}" + (f" · {summary}" if summary else ""))
    if not found:
        lines.append("- none found under the investigation location, `.scratch/`, or `docs/`")
    if capped:
        lines.append(f"- scan stopped after {CAP} Markdown files; narrow the project directory")
    lines += ["", "## Markers"]
    lines += [f"- {name}: {'yes' if present else 'no'}" for name, present in markers(root)]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".", help="project directory (default: current directory)")
    args = parser.parse_args()
    try:
        print(report(args.project))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")

#!/usr/bin/env python3
"""Seed and check the coverage ledger for a change.

Seed writes JSON to stdout: one unit per changed symbol, or per hunk when no
symbol encloses it, with the consumers outside the change that reference the
symbol, nearest directory first and vendored or generated files excluded. A
prose, configuration, or other non-source file gets one unit per file and the
text class. Units come from the pinned diff, so two runs on the same pins start
from the same list. With --base omitted the comparison is the working tree
against HEAD, including untracked files. --coarse merges source units per file
for a bounded pass on a large diff. --prior carries an earlier ledger's
dispositions as leads, never as closure. Save the output at the investigation
location, then record each unit's disposition in it.

Check reads that saved ledger and reports the units, classes, and change checks
with no disposition. Exit 0 when every unit has a disposition and every closed
unit carries a full sweep; exit 1 when coverage is incomplete; exit 2 for
invalid inputs or failed Git operations. Seed writes no files.

Definition patterns cover common Python, JavaScript, TypeScript, Go, Rust,
Java, Ruby, and PHP idioms; a language outside that list gets hunk units.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

CLASSES = ("boundary", "errors", "state", "consumers", "concurrency", "normalization", "cost", "compatibility")
TEXT_CLASSES = ("text",)
CODE_SUFFIXES = {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".kts",
                 ".rb", ".php", ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".cs", ".swift", ".m", ".mm", ".scala",
                 ".sh", ".bash", ".zsh", ".sql", ".vue", ".svelte", ".dart", ".ex", ".exs", ".erl", ".hs", ".lua",
                 ".pl", ".pm", ".r", ".jl", ".groovy", ".tf", ".proto", ".graphql", ".sol", ".zig", ".nim", ".v"}
CHANGE_CHECKS = ("untested lines", "weakened checks", "dependency compatibility", "static deltas",
                 "history and review context", "caller hypotheses")
TERMINAL = ("closed", "candidate", "blocked", "deferred", "out_of_scope")
CHECK_DONE = ("done", "not applicable", "not run")
GAP_DONE = ("clean", "not run")
CONSUMER_CAP = 12
DEFINITIONS = (
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)"),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"),
    re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:public|private|protected|internal|static|final|abstract|sealed|override|virtual|async|partial|\s)*"
               r"[A-Za-z_][\w<>\[\],.?\s]*\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:const\s*)?\{"),
    re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?(?:class|interface|struct|enum|trait|type)\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?function\s+([A-Za-z_]\w*)"),
)
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git failed with exit {result.returncode}")
    return result.stdout


def indent(text):
    expanded = text.expandtabs(8)
    return len(expanded) - len(expanded.lstrip())


def definitions(lines):
    found = []
    for number, text in enumerate(lines, 1):
        for pattern in DEFINITIONS:
            match = pattern.match(text)
            if match:
                found.append((number, indent(text), match.group(1)))
                break
    return found


def enclosing(defs, number, depth):
    for line, own, name in reversed(defs):
        if line == number:
            return name
        if line < number and own < depth:
            return name
    return None


def ranges(numbers):
    collapsed = []
    for number in sorted(set(numbers)):
        if collapsed and number == collapsed[-1][1] + 1:
            collapsed[-1][1] = number
        else:
            collapsed.append([number, number])
    return collapsed


def parse(diff):
    files, current, hunk, header = [], None, None, False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            header, current, hunk = True, None, None
            continue
        if header and line.startswith("--- "):
            old = None if line == "--- /dev/null" else line[4:]
            current = {"old_path": old, "path": old, "hunks": []}
            files.append(current)
            continue
        if header and line.startswith("+++ "):
            if line != "+++ /dev/null":
                current["path"] = line[4:]
            current["change"] = "added" if current["old_path"] is None else (
                "deleted" if line == "+++ /dev/null" else "modified")
            continue
        match = HUNK.match(line)
        if match and current is not None:
            header = False
            hunk = {"old": int(match.group(1)), "new": int(match.group(3)), "added": [], "removed": []}
            current["hunks"].append(hunk)
            continue
        if header or current is None or hunk is None or not line or line[0] not in "+-":
            continue
        if line[0] == "+":
            hunk["added"].append((hunk["new"], line[1:]))
            hunk["new"] += 1
        else:
            hunk["removed"].append((hunk["old"], line[1:]))
            hunk["old"] += 1
    return files


def content(repo, rev, path):
    if path is None:
        return []
    if rev is None:
        target = Path(repo) / path
        return target.read_text(encoding="utf-8", errors="replace").splitlines() if target.is_file() else []
    try:
        return git(repo, "show", f"{rev}:{path}").splitlines()
    except ValueError:
        return []


def body(lines, defs, symbol):
    start = next((number for number, _, name in defs if name == symbol), None)
    if start is None:
        return "\n".join(lines)
    depth = indent(lines[start - 1])
    end = len(lines)
    for number, own, _ in defs:
        if number > start and own <= depth:
            end = number - 1
            break
    return "\n".join(lines[start - 1:end])


def digest(text):
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def consumers(repo, rev, symbols, changed, cache, path):
    found = []
    for symbol in symbols:
        if symbol not in cache:
            args = ("grep", "-l", "-w", symbol, rev) if rev else ("grep", "-l", "-w", "--untracked", symbol)
            try:
                listing = git(repo, *args)
            except ValueError:
                listing = ""
            cache[symbol] = [line.split(":", 1)[-1] if rev else line for line in listing.splitlines()]
        found += [candidate for candidate in cache[symbol]
                  if candidate not in changed and candidate not in found and worth_reading(candidate)]
    home = PurePosixPath(path).parent
    return sorted(found, key=lambda candidate: (PurePosixPath(candidate).parent != home,
                                                PurePosixPath(candidate).parts[0] != (home.parts[0] if home.parts else ""),
                                                candidate))


def worth_reading(path):
    parts = PurePosixPath(path)
    if parts.suffix.lower() not in CODE_SUFFIXES:
        return False
    if {"node_modules", "vendor", "dist", "build", "__pycache__", "assets", "generated"} & set(parts.parts):
        return False
    return not path.endswith((".min.js", ".min.css", ".map", ".pb.go", "_pb2.py"))


def seed(repo, base, head, coarse, prior_path):
    if base is None:
        diff = git(repo, "diff", "--unified=0", "--no-color", "--no-prefix", "--no-ext-diff", "HEAD")
        untracked = git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
    else:
        diff = git(repo, "diff", "--unified=0", "--no-color", "--no-prefix", "--no-ext-diff", f"{base}..{head}")
        untracked = []
    files = parse(diff)
    for path in untracked:
        files.append({"old_path": None, "path": path, "change": "added",
                      "hunks": [{"old": 0, "new": 1, "added": list(enumerate(content(repo, None, path), 1)), "removed": []}]})
    changed = {file["path"] for file in files}
    base_rev, head_rev = ("HEAD" if base is None else base), (None if base is None else head)
    prior = {}
    if prior_path:
        prior = {unit["id"]: unit for unit in json.loads(Path(prior_path).read_text()).get("units", [])}
    cache, units = {}, []
    for file in files:
        path = file["path"]
        is_code = PurePosixPath(path).suffix.lower() in CODE_SUFFIXES
        per_file = coarse or not is_code
        head_lines = content(repo, head_rev, path)
        base_lines = content(repo, base_rev, file["old_path"])
        head_defs, base_defs = definitions(head_lines), definitions(base_lines)
        head_names = {name for _, _, name in head_defs}
        base_names = {name for _, _, name in base_defs}
        grouped, changed_names, blank = {}, [], []
        for index, hunk in enumerate(file["hunks"], 1):
            for side, lines, defs in (("added", head_lines, head_defs), ("removed", base_lines, base_defs)):
                for number, text in hunk[side]:
                    if not text.strip():
                        blank.append((side, number, text))
                        continue
                    symbol = enclosing(defs, number, indent(text))
                    if symbol and symbol not in changed_names:
                        changed_names.append(symbol)
                    key = path if per_file else (symbol or f"hunk-{index}")
                    entry = grouped.setdefault(key, {"symbol": None if per_file else symbol, "added": [], "removed": []})
                    entry[side].append((number, text))
        if not grouped and blank:
            entry = grouped.setdefault(path if per_file else "hunk-1",
                                       {"symbol": None, "added": [], "removed": []})
            for side, number, text in blank:
                entry[side].append((number, text))
        for key, entry in grouped.items():
            symbol = entry["symbol"]
            if per_file:
                unit_id, kind = f"{path}::file", file["change"]
                text = "\n".join(head_lines) or "\n".join(base_lines)
                names = changed_names if is_code else []
            elif symbol:
                unit_id = f"{path}::{symbol}"
                kind = file["change"] if file["change"] != "modified" else (
                    "modified" if symbol in head_names and symbol in base_names else
                    "added" if symbol in head_names else "deleted")
                lines = head_lines if symbol in head_names else base_lines
                defs = head_defs if symbol in head_names else base_defs
                text = body(lines, defs, symbol)
                names = [symbol]
            else:
                unit_id, kind = f"{path}::{key}", file["change"]
                text = "\n".join(text for _, text in entry["added"] + entry["removed"])
                names = []
            listed = consumers(repo, head_rev, names, changed, cache, path)
            previous = prior.get(unit_id)
            units.append({
                "id": unit_id, "path": path, "symbol": symbol, "change": kind,
                "lines": ranges([number for number, _ in entry["added"]]),
                "removed_lines": ranges([number for number, _ in entry["removed"]]),
                "source_hash": digest(text), "classes": list(CLASSES if is_code else TEXT_CLASSES),
                "consumers": listed[:CONSUMER_CAP], "consumers_truncated": len(listed) > CONSUMER_CAP,
                "status": "planned", "sweep": {}, "reviewed": [], "findings": [], "unresolved": [], "reason": "",
                "prior": None if previous is None else {
                    "disposition": previous.get("status"), "source_unchanged": previous.get("source_hash") == digest(text),
                    "unresolved": previous.get("unresolved", []), "reason": previous.get("reason", "")},
            })
    units.sort(key=lambda unit: unit["id"])
    prior_gaps = [{"id": unit["id"], "reason": unit.get("reason") or "; ".join(unit.get("unresolved", []))}
                  for unit in prior.values()
                  if unit.get("status") in ("blocked", "deferred", "out_of_scope") or unit.get("unresolved")]
    return {
        "pins": {"repo": str(Path(repo).resolve()), "base": base or "HEAD (working tree)", "head": head or "working tree",
                 "base_sha": git(repo, "rev-parse", "--verify", f"{base_rev}^{{commit}}").strip(),
                 "head_sha": git(repo, "rev-parse", "--verify", "HEAD^{commit}").strip() if head_rev is None else
                 git(repo, "rev-parse", "--verify", f"{head_rev}^{{commit}}").strip(),
                 "granularity": "file" if coarse else "symbol", "prior_ledger": prior_path},
        "classes": list(CLASSES) + list(TEXT_CLASSES), "units": units,
        "change_checks": [{"name": name, "status": "planned", "note": ""} for name in CHANGE_CHECKS],
        "gap_check": {"status": "not run", "note": ""},
        "prior_gaps": prior_gaps,
    }


def check(ledger):
    default = ledger.get("classes") or list(CLASSES)
    problems, gaps, closed, findings = [], [], 0, 0
    for unit in ledger.get("units", []):
        name, status = unit.get("id", "<no id>"), unit.get("status")
        classes = unit.get("classes") or default
        if status not in TERMINAL:
            problems.append(f"{name}: status is {status!r}, not a disposition")
            continue
        if status in ("closed", "candidate"):
            missing = [item for item in classes if not str(unit.get("sweep", {}).get(item, "")).strip()]
            if missing:
                problems.append(f"{name}: no sweep clause for {', '.join(missing)}")
            if not unit.get("reviewed"):
                problems.append(f"{name}: no reviewed source")
            if unit.get("unresolved"):
                problems.append(f"{name}: closed with an unresolved fact")
            if status == "candidate" and not unit.get("findings"):
                problems.append(f"{name}: candidate without a finding")
            closed += 1
            findings += len(unit.get("findings", []))
        else:
            if not str(unit.get("reason", "")).strip():
                problems.append(f"{name}: {status} without a reason")
            gaps.append(f"{name}: {status} — {unit.get('reason', '')}")
    for item in ledger.get("change_checks", []):
        if item.get("status") not in CHECK_DONE or not str(item.get("note", "")).strip():
            problems.append(f"change check {item.get('name')!r}: no result and note")
        elif item["status"] == "not run":
            gaps.append(f"change check {item['name']}: not run — {item['note']}")
    gap = ledger.get("gap_check", {})
    if gap.get("status") == "worked":
        problems.append("gap check: gaps were worked, but no later pass accepted nothing")
    elif gap.get("status") not in GAP_DONE or not str(gap.get("note", "")).strip():
        problems.append("gap check: no result and note")
    elif gap["status"] == "not run":
        gaps.append(f"gap check: not run — {gap['note']}")
    lines = []
    if problems:
        lines.append(f"Incomplete coverage: {len(problems)} problems")
        lines += [f"- {problem}" for problem in problems]
    else:
        lines.append(f"Every unit has a disposition: {closed} closed, {findings} findings recorded.")
    if gaps:
        lines.append("")
        lines.append(f"Gaps to state in the delivery ({len(gaps)}):")
        lines += [f"- {gap}" for gap in gaps]
    return "\n".join(lines), 1 if problems else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--coarse", action="store_true")
    parser.add_argument("--prior", metavar="LEDGER")
    parser.add_argument("--check", metavar="LEDGER")
    args = parser.parse_args(argv)
    if args.check:
        try:
            report, code = check(json.loads(Path(args.check).read_text()))
        except (OSError, ValueError, AttributeError, TypeError) as error:
            parser.exit(2, f"{error}\n")
        print(report)
        raise SystemExit(code)
    if not args.head and args.base is not None:
        parser.exit(2, "--head is required with --base\n")
    try:
        ledger = seed(args.repo, args.base, args.head, args.coarse, args.prior)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(ledger, indent=1))


if __name__ == "__main__":
    main()

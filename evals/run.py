#!/usr/bin/env python3
"""Run evals/<case>/ cases with `claude -p` on scratch copies of each fixture, then grade them.

`claude plugin eval` runs shell commands read-only and without git, which these
skills need, so this runner reads the same case files (prompt.md frontmatter,
case.yaml scaffold_script, graders/*.md) and runs them unsandboxed.

  python3 evals/run.py --plugin-dir <checkout> --out <dir> [--case <glob>] [--runs 3] [--model M] [-j 4]

Each run is an unsandboxed `claude -p` session with Bash, as you, on your
machine. Run it only on this repository's own plugin and cases.

Graders: regex (target last_message | trace), tool_used (tool, input_match, min, max),
file_exists (path glob over files the run created), llm (body is the rubric; judged
once by --judge-model). Here "trace" is what the agent wrote and ran (assistant text
and tool inputs), never tool results, so text it only read cannot match.
"""
import argparse
import concurrent.futures
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent


def front(path):
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}, text
    head, body = text[4:].split("\n---\n", 1)
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            value = value.strip()
            if value[:1] == '"' and value[-1:] == '"':
                value = value[1:-1].replace("\\\\", "\\")  # YAML double quotes escape backslashes
            elif value[:1] == "'" and value[-1:] == "'":
                value = value[1:-1]
            meta[key.strip()] = value
    return meta, body.strip()


def load_case(case_dir):
    meta, prompt = front(case_dir / "prompt.md")
    scaffold = re.search(r"scaffold_script:\s*(\S+)", (case_dir / "case.yaml").read_text())
    graders = [(g.stem, *front(g)) for g in sorted((case_dir / "graders").glob("*.md"))]
    tools = meta.get("allowed_tools", "[Read, Grep, Glob, Write, Edit, Skill, Bash]").strip("[]").replace(" ", "")
    return dict(name=case_dir.name, dir=case_dir, prompt=prompt, tools=tools,
                max_turns=meta.get("max_turns", "70"), scaffold=scaffold and case_dir / scaffold.group(1),
                graders=graders)


def files(root):
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts}


def parse_stream(path):
    final, written, tool_calls, info = "", [], [], {}
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant":
            for item in event["message"]["content"]:
                if item.get("type") == "text":
                    written.append(item["text"])
                elif item.get("type") == "tool_use":
                    tool_calls.append((item["name"], json.dumps(item["input"])))
                    written.append(json.dumps(item["input"]))
        elif event.get("type") == "result":
            final = event.get("result") or ""
            info = {k: event.get(k) for k in ("num_turns", "total_cost_usd", "is_error")}
    return final, "\n".join(written), tool_calls, info


def judge(rubric, final, model):
    prompt = ("Grade an AI agent's final message against a rubric. Give one or two sentences of reason, then end "
              "with a last line that is exactly VERDICT: PASS or VERDICT: FAIL.\n\n## Rubric\n\n" + rubric
              + "\n\n## Final message\n\n" + final)
    out = subprocess.run(["claude", "-p", "--model", model, "--setting-sources", "", "--strict-mcp-config",
                          "--max-turns", "1", "--settings", '{"disableAllHooks":true}'],
                         input=prompt, capture_output=True, text=True, timeout=300).stdout.strip()
    verdicts = re.findall(r"VERDICT:\s*(PASS|FAIL)", out)
    return bool(verdicts) and verdicts[-1] == "PASS", out[:300]


def grade(graders, final, trace, tool_calls, created, judge_model):
    results = {}
    for name, meta, body in graders:
        kind = meta["type"]
        if kind == "regex":
            flags = re.I if "i" in meta.get("flags", "") else 0
            flags |= re.M if "m" in meta.get("flags", "") else 0
            hit = re.search(meta["pattern"], trace if meta.get("target") == "trace" else final, flags) is not None
            ok, why = (not hit, "absent") if meta.get("match") == "not_contains" else (hit, "matched" if hit else "no match")
        elif kind == "tool_used":
            count = sum(1 for tool, args in tool_calls if tool == meta["tool"]
                        and re.search(meta.get("input_match", ""), args))
            low, high = int(meta.get("min", 1)), int(meta.get("max", 10**9))
            ok, why = low <= count <= high, f"{count} matching calls, expected {low}..{high}"
        elif kind == "file_exists":
            hits = [f for f in created if fnmatch.fnmatch(f, meta["path"])]
            want = meta.get("exists", "true") != "false"
            ok, why = bool(hits) == want, ", ".join(hits[:3]) or "none created"
        elif kind == "llm":
            ok, why = judge(body, final, judge_model)
        else:
            ok, why = False, f"unsupported grader type {kind}"
        results[name] = {"passed": ok, "why": why}
    return results


def run_one(case, run, args):
    work = Path(args.out) / f"{case['name']}-{run}"
    work.mkdir(parents=True)
    if case["scaffold"]:
        subprocess.run(["bash", str(case["scaffold"])], cwd=work, check=True, capture_output=True)
    before = files(work)
    stream = work.parent / f"{work.name}.jsonl"
    with open(stream, "w") as out:
        subprocess.run(["claude", "-p", case["prompt"], "--plugin-dir", args.plugin_dir, "--model", args.model,
                        "--setting-sources", "", "--settings", '{"disableAllHooks":true}', "--strict-mcp-config",
                        "--allowedTools", case["tools"], "--disallowedTools", "Bash(gh:*),Bash(git push:*)",
                        "--permission-mode", "acceptEdits", "--max-turns", case["max_turns"],
                        "--output-format", "stream-json", "--verbose"],
                       cwd=work, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.DEVNULL, timeout=3600)
    final, trace, tool_calls, info = parse_stream(stream)
    created = sorted(files(work) - before)
    return {"case": case["name"], "run": run, **info, "final": final, "created": created,
            "graders": grade(case["graders"], final, trace, tool_calls, created, args.judge_model)}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--plugin-dir")
    parser.add_argument("--out", required=True, help="new directory for workspaces, streams and results.json")
    parser.add_argument("--regrade", action="store_true",
                        help="re-judge the llm graders of an existing --out with the current rubrics; no agent runs")
    parser.add_argument("--case", default="*")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--model", default="claude-opus-5-5")
    parser.add_argument("--judge-model", default="claude-sonnet-5-5")
    parser.add_argument("-j", "--jobs", type=int, default=4)
    args = parser.parse_args()
    cases = [load_case(d) for d in sorted(EVALS.iterdir())
             if (d / "prompt.md").exists() and fnmatch.fnmatch(d.name, args.case)]
    out = Path(args.out) / "results.json"
    if args.regrade:
        results = json.loads(out.read_text())
        by_name = {c["name"]: c for c in cases}

        def regrade(r):
            llm = [g for g in by_name[r["case"]]["graders"] if g[1]["type"] == "llm"]
            r["graders"].update(grade(llm, r["final"], "", [], [], args.judge_model))
            return r
        with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
            results = list(pool.map(regrade, [r for r in results if r["case"] in by_name]))
    else:
        if not args.plugin_dir:
            parser.error("--plugin-dir is required unless --regrade")
        args.plugin_dir = str(Path(args.plugin_dir).resolve())
        Path(args.out).mkdir(parents=True, exist_ok=False)
        jobs = [(c, r) for c in cases for r in range(args.runs)]
        with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
            results = list(pool.map(lambda job: run_one(*job, args), jobs))
    out.write_text(json.dumps(results, indent=1))
    for case in cases:
        runs = [r for r in results if r["case"] == case["name"]]
        cost = sum(r.get("total_cost_usd") or 0 for r in runs)
        print(f"{case['name']}  ${cost:.2f}")
        for name, *_ in case["graders"]:
            print(f"  {name:28} " + "".join("P" if r["graders"][name]["passed"] else "F" for r in runs))


if __name__ == "__main__":
    sys.exit(main())

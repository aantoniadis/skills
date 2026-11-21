"""workflow_state.py reports the Git position and classifies our skills' notes by the `kind:` in their
front matter, else by their template's marker line. Inside herdr-core it also lists the project's sessions."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/whats-next/scripts/workflow_state.py"
TEMPLATES = {  # kind -> the template or fixture every real artifact is filled from
    "understanding note (explain)": ROOT / "skills/explain/references/understanding-template.md",
    "plan (plan-change)": ROOT / "skills/plan-change/references/plan-template.md",
    "diagnosis note (fix-bug)": ROOT / "tests/fixtures/diagnosis/diagnosis.md",
    "PR review guide (pr-review-guide)": ROOT / "skills/pr-review-guide/references/report-template.md",
    "acceptance report (check-acceptance)": ROOT / "skills/check-acceptance/references/report-template.md",
}


def run(*args, cwd, env=None):
    result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    return result.stdout


class WorkflowStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # The suite can run inside herdr-core; only the session tests may see it.
        self.env = {**{k: v for k, v in os.environ.items() if not k.startswith("HC_")}, "XDG_STATE_HOME": str(self.root / "state")}
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["bash", "-c", "git init -q -b main && echo a > a && git add . && git -c user.email=t@t -c user.name=t commit -qm init"
                        " && git checkout -q -b feat/x && echo b > b && git add b && git -c user.email=t@t -c user.name=t commit -qm two && echo c > c"],
                       cwd=self.repo, check=True)

    def test_git_position_and_classified_notes(self):
        for index, (kind, template) in enumerate(TEMPLATES.items()):
            target = self.repo / (".scratch" if index % 2 else "docs") / f"n{index}" / template.name
            target.parent.mkdir(parents=True)
            shutil.copy(template, target)
        (self.repo / "docs/plain.md").write_text("# Plain\n\nNo marker here.\n")
        out = run(str(self.repo), cwd=self.root, env=self.env)
        self.assertIn("- Branch: `feat/x` (upstream: none) · ahead of main by 1, behind by 0 · 3 uncommitted files · last commit: ", out)
        self.assertIn("- Investigation location: `" + str(self.repo.resolve() / ".scratch") + "` (default)", out)
        for kind, template in TEMPLATES.items():
            self.assertRegex(out, rf"(?m)^- {re.escape(kind)}: `(?:docs|\.scratch)/n\d/{re.escape(template.name)}` · \d{{4}}-\d\d-\d\d", kind)
        self.assertNotIn("plain.md", out)
        self.assertIn("- Local tool record (", out)
        self.assertNotIn("## Sessions", out, "no session list outside herdr-core")
        self.assertFalse((self.root / "state").exists(), "the scan must create nothing")

    def test_recorded_location_tickets_and_summary(self):
        (self.repo / "AGENTS.md").write_text("- **Investigations:** `docs/inv`\n")
        plan = self.repo / "docs/inv/order/plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("# Order\n\n**Readiness:** one slice blocked on the retry decision.\n\n## Delivery slices\n")
        (self.repo / ".scratch/order/issues").mkdir(parents=True)
        out = run(str(self.repo), cwd=self.root, env=self.env)
        self.assertIn("(recorded)", out)
        self.assertIn("- plan (plan-change): `docs/inv/order/plan.md` · ", out)
        self.assertIn(" · one slice blocked on the retry decision.", out)
        self.assertIn("- Local tickets (.scratch/order/issues): yes", out)

    def test_recorded_location_outside_the_checkout(self):
        (self.repo / "AGENTS.md").write_text("- Investigations: ../inv\n")
        plan = self.root / "inv/order/plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("# Order\n\n## Delivery slices\n")
        out = run(str(self.repo), cwd=self.root, env=self.env)
        self.assertIn(f"- plan (plan-change): `{plan.resolve()}` · ", out)

    def test_kind_front_matter_outranks_markers(self):
        notes = self.repo / ".scratch/n"
        notes.mkdir(parents=True)
        # A plan whose author removed Delivery slices is still a plan; a note that declares a kind is that kind
        # even when it carries another template's marker; an unknown kind falls back to nothing, not to a marker.
        (notes / "plan.md").write_text("---\nkind: plan\nhead: abc\n---\n# Rename\n\n**Readiness:** ready.\n")
        (notes / "note.md").write_text("---\nkind: understanding-note\n---\n# Flow\n\n## What the change does\n")
        (notes / "odd.md").write_text("---\nkind: recipe\n---\n# Odd\n\n## Delivery slices\n")
        out = run(str(self.repo), cwd=self.root, env=self.env)
        self.assertIn("- plan (plan-change): `.scratch/n/plan.md` · ", out)
        self.assertIn(" · ready.", out)
        self.assertIn("- understanding note (explain): `.scratch/n/note.md` · ", out)
        self.assertNotIn("odd.md", out)

    def herdr_core(self, terminals):
        """A stub `hc` that answers `ls` and `get` from `terminals`, logs every call, and fails for an unknown address."""
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        (self.root / "terminals.json").write_text(json.dumps(terminals))
        stub = bin_dir / "hc"
        stub.write_text(f"""#!{sys.executable}
import json, sys
args = [a for a in sys.argv[1:] if a != "--json"]
open({str(self.root / "hc.log")!r}, "a").write(" ".join(args) + "\\n")
terminals = json.load(open({str(self.root / "terminals.json")!r}))
if args == ["ls"]:
    print(json.dumps({{"hidden_finished": 0, "terminals": [{{"address": t["address"]}} for t in terminals]}}))
elif args[0] == "get" and any(t["address"] == args[1] for t in terminals):
    print(json.dumps(next(t for t in terminals if t["address"] == args[1])))
else:
    sys.exit('{{"error":{{"kind":"not_found","message":"no terminal"}}}}')
""")
        stub.chmod(0o755)
        return {**self.env, "PATH": f"{bin_dir}{os.pathsep}{self.env['PATH']}", "HC_TERMINAL_ID": "t1"}

    def test_sessions_of_the_project_inside_herdr_core(self):
        here = str(self.repo.resolve())
        env = self.herdr_core([
            # `cwd` is the launch folder: this session started elsewhere and works in the project now.
            {"address": "t1", "name": None, "cwd": "/elsewhere", "foreground": {"cwd": here}, "parent": None, "die_with_parent": False,
             "status": {"app": "claude-code", "state": "working"}, "turn": 4, "title": "Plan the export",
             "labels": {"herdr.space": "sp9", "herdr.tab": "tb1", "where": "repo / 1"}},
            {"address": "t2", "name": "find-bugs-export", "cwd": here, "foreground": None, "parent": "t1", "die_with_parent": True,
             "status": {"app": "claude-code", "state": "done"}, "turn": 1, "title": None, "labels": {"step": "find-bugs", "for": "feat/x"}},
            {"address": "t3", "name": "implement-t1", "cwd": here + "/sub", "foreground": {"cwd": here + "/sub"}, "parent": "t1",
             "die_with_parent": False, "status": None, "turn": 0, "argv": ["/usr/bin/codex"], "labels": {}},
            {"address": "t4", "name": None, "cwd": "/other/project", "foreground": {"cwd": "/other/project"}, "parent": None,
             "die_with_parent": False, "status": {"app": "claude-code", "state": "done"}, "turn": 9, "labels": {}},
        ])
        out = run(str(self.repo), cwd=self.root, env=env)
        self.assertIn('- `t1` (this session) · claude-code · working, turn 4 · opened by the user · "Plan the export" · space `sp9`', out)
        self.assertIn("- `t2` find-bugs-export · claude-code · done, turn 1 · started by `t1`, ends with it · for=feat/x step=find-bugs", out)
        self.assertIn("- `t3` implement-t1 · codex · no status, turn 0 · started by `t1`, outlives it", out)
        self.assertNotIn("`t4`", out, "a session of another project is not listed")
        calls = (self.root / "hc.log").read_text().split("\n")
        self.assertTrue(all(call.split()[0] in ("ls", "get") for call in calls if call), f"the scan only reads: {calls}")

    def test_hc_failure_is_reported_not_raised(self):
        env = self.herdr_core([])
        (self.root / "bin/hc").write_text("#!/bin/sh\necho 'core is not running' >&2\nexit 1\n")
        out = run(str(self.repo), cwd=self.root, env=env)
        self.assertIn("## Sessions in herdr-core\n- `hc` did not answer, so the sessions are unknown: core is not running", out)
        self.assertIn("- Branch: `feat/x`", out)

    def test_outside_git(self):
        plain = self.root / "plain"
        plain.mkdir()
        out = run(str(plain), cwd=self.root, env=self.env)
        self.assertIn("- Not a Git checkout", out)
        self.assertIn("- none found", out)
        self.assertFalse((plain / ".scratch").exists())


if __name__ == "__main__":
    unittest.main()

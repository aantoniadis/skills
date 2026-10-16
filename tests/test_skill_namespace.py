"""Run with python3 tests/test_skill_namespace.py [--runtimes]. Stdlib only."""

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "aantoniadis-skills"


def original_skills():
    """Name -> owner for the originals listed in setup-tools' reference, one section per owner."""
    text = (ROOT / "skills/setup-tools/references/upstream-skills.md").read_text()
    found = {}
    for heading, owner in (("Matt Pocock's skills", "mattpocock"), ("HumanLayer's skills", "humanlayer")):
        section = text.split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]
        for name in re.findall(r"`([a-z][a-z0-9-]*)`", section):
            found.setdefault(name, owner)
    return found


def check_references():
    upstream = original_skills()
    skills = {p.parent.name: p for p in ROOT.glob("skills/**/SKILL.md")}
    for name in upstream:
        assert name not in skills, name  # originals are never bundled
    for name, path in skills.items():
        text = path.read_text()
        assert re.search(rf"^name: {re.escape(name)}$", text, re.M), path
        # Use the hosts' normal discovery and invocation defaults.
        frontmatter = text.split("\n---\n", 1)[0]
        assert "disable-model-invocation:" not in frontmatter, path
        policy = path.parent / "agents/openai.yaml"
        assert not policy.exists(), policy
        body = text.split("\n---\n", 1)[1]
        if PACKAGE + ":" in body or "mattpocock:" in body or "humanlayer:" in body:
            assert "[package references](../REFERENCES.md)" in body, path
    versions = set()
    for runtime in (".codex-plugin", ".claude-plugin"):
        manifest = json.loads((ROOT / runtime / "plugin.json").read_text())
        assert manifest["name"] == PACKAGE
        assert manifest["skills"] == "./skills/"
        versions.add(manifest["version"])
    assert set(skills) == {"setup-tools", "explain", "plan-change", "find-bugs", "pr-review-guide", "fix-bug"}
    versions.add(json.loads((ROOT / "package.json").read_text())["version"])  # the OpenCode package
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert marketplace["name"] == "aantoniadis"
    assert marketplace["plugins"][0]["name"] == PACKAGE
    assert marketplace["plugins"][0]["source"] == "./"
    # One version: Claude reads plugin.json first, and Codex reads only its own manifest.
    assert len(versions) == 1 and "version" not in marketplace["plugins"][0], versions

    documents = [ROOT / "README.md", ROOT / "AGENTS.md", *ROOT.glob("docs/*.md"),
                 *ROOT.glob("skills/**/*.md"), *ROOT.glob("skills/**/*.yaml")]
    for path in documents:
        if "node_modules" in path.parts:
            continue
        text = path.read_text()
        for name in re.findall(r"aantoniadis-skills:([a-z][a-z0-9-]*)", text):
            assert name in skills, (path, name)
        for owner, name in re.findall(r"(mattpocock|humanlayer):([a-z][a-z0-9-]*)", text):
            assert upstream.get(name) == owner, (path, owner, name)
        for marker, name, following in re.findall(r"(?<![\w:/-])([/$])([a-z][a-z0-9-]*)([:/]?)", text):
            if following == "/":  # Filesystem paths and application routes.
                continue
            assert name not in skills, (path, marker + name)
        prose = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", "", text)
        for target in re.findall(r"\]\(([^\s)]+)\)", prose):
            if "://" in target or target.startswith(("#", "/")):
                continue
            assert (path.parent / target.split("#", 1)[0]).exists(), (path, target)
    # Authoring conventions from AGENTS.md "Skill authoring checklist": a third-person trigger description
    # with "Use when" and "Not for", an argument hint, one preamble, a bounded body, and a contents list on long references.
    for name, path in skills.items():
        front, body = path.read_text().split("\n---\n", 1)
        description = re.search(r"^description: (.+)$", front, re.M).group(1)
        # A plain YAML scalar cannot hold ": " or " #"; strict parsers such as GitHub's reject it.
        if description.startswith('"'):
            description = description[1:-1]
        else:
            assert ": " not in description and " #" not in description, (name, "quote the description")
        assert len(description) <= 1024 and re.match(r"[A-Z][a-z]+s[ ,]", description), (name, description[:60])
        assert "Use when" in description and "Not for" in description, (name, description[:60])
        assert re.search(r"^argument-hint: ", front, re.M), name
        assert body.lstrip().startswith("For helper loading, follow [package references](../REFERENCES.md)."), name
        assert body.count("\n") < 500, name
    for path in ROOT.glob("skills/**/*.md"):
        if "node_modules" in path.parts or "assets" in path.parts or path.name in ("SKILL.md",) or path.name.endswith("-template.md"):
            continue
        if path.read_text().count("\n") > 100:
            assert "\n## Contents\n" in path.read_text(), path
    assert "mattpocock:implement" in skills["plan-change"].read_text()
    # Naming an upstream helper does not run it: every sentence in a skill that names one says to invoke it
    # (model-invoked) or hand off to it (user-invoked), never to load its files; REFERENCES.md defines both.
    for path in [*ROOT.glob("skills/*/SKILL.md"), *ROOT.glob("skills/*/references/*.md")]:
        prose = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", "", path.read_text())
        for sentence in re.split(r"(?<=[.!?])\s+|\n\s*\n", prose):
            if re.search(r"(mattpocock|humanlayer):[a-z]", sentence):
                assert re.search(r"\b([Ii]nvoke[sd]?|[Hh]and(s|ed)? off)\b", sentence), (path, sentence.strip()[:120])
                assert not re.search(r"\b[Ll]oad(s|ed|ing)?\b", sentence), (path, sentence.strip()[:120])
    # Every claim carries its evidence: each skill, and every reference that has the agent draw a diagram, points at the rule.
    for path in ROOT.glob("skills/**/*.md"):
        if "node_modules" in path.parts:
            continue
        if path.name in ("EVIDENCE.md", "TECHNICAL-ENGLISH.md", "CODE-TOOLS.md"):  # the rule itself, a prose category, a tool row
            continue
        if path.name == "SKILL.md" or re.search(r"\bdiagram", path.read_text(), re.I):
            assert "EVIDENCE.md" in path.read_text(), path
    assert len(upstream) == 9, sorted(upstream)
    print(f"Names, package references, manifests, links, and provenance: {len(skills)} skills / {len(upstream)} original skills passed")


class JsonProcess:
    """Read runtime metadata only; no user turn or model request is submitted."""

    def __init__(self, args, cwd, env=None):
        self.process = subprocess.Popen(args, cwd=cwd, env=env, text=True,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
        self.messages = queue.Queue()
        def read():
            for line in self.process.stdout:
                self.messages.put(json.loads(line))
        threading.Thread(target=read, daemon=True).start()

    def request(self, message, matches):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        while True:
            response = self.messages.get(timeout=40)
            if matches(response):
                return response

    def close(self):
        self.process.terminate()
        self.process.wait(timeout=5)


def check_runtimes():
    assert shutil.which("codex") and shutil.which("claude"), "--runtimes requires both CLIs"
    with tempfile.TemporaryDirectory(prefix="plugin discovery ") as tmp:
        root = Path(tmp)
        ours = root / "plugins" / PACKAGE
        ours.mkdir(parents=True)
        for name in ("skills", ".codex-plugin", ".claude-plugin"):
            shutil.copytree(ROOT / name, ours / name)
        other = root / "plugins/mattpocock-skills"
        (other / ".claude-plugin").mkdir(parents=True)
        (other / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "mattpocock-skills", "version": "0.1.0"}))
        for name in ("pr-review-guide", "find-bugs"):
            path = other / "skills" / name
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Synthetic collision fixture.\n---\n\nOTHER-PACKAGE\n")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin/marketplace.json").write_text(json.dumps({
            "name": "namespace-check", "owner": {"name": "Test"}, "plugins": [
                {"name": p.name, "source": "./plugins/" + p.name} for p in (ours, other)]}))
        config = root / "codex-home"
        config.mkdir()
        env = {**os.environ, "CODEX_HOME": str(config)}
        for args in (("marketplace", "add", str(root)), ("add", PACKAGE + "@namespace-check"),
                     ("add", "mattpocock-skills@namespace-check")):
            subprocess.run(["codex", "plugin", *args], env=env, cwd=root, timeout=40,
                           check=True, capture_output=True)
        process = JsonProcess(["codex", "app-server", "--stdio"], root, env)
        try:
            process.request({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "namespace-check", "version": "1.0.0"},
                "capabilities": {"experimentalApi": True}}}, lambda r: r.get("id") == 1)
            response = process.request({"id": 2, "method": "skills/list", "params": {
                "cwds": [str(root)], "forceReload": True}}, lambda r: r.get("id") == 2)
            group = response["result"]["data"][0]
            assert not group["errors"], group["errors"]
            skills = {s["name"]: s for s in group["skills"]}
            for owner in (PACKAGE, "mattpocock-skills"):
                for name in ("pr-review-guide", "find-bugs"):
                    skill = skills[owner + ":" + name]
                    assert skill["enabled"] and skill["pluginId"] == owner + "@namespace-check"
            loaded = Path(skills[PACKAGE + ":pr-review-guide"]["path"])
            helper = (loaded.parent / "../find-bugs/SKILL.md").resolve()
            assert helper == Path(skills[PACKAGE + ":find-bugs"]["path"])
            assert helper.read_text() == (ROOT / "skills/find-bugs/SKILL.md").read_text()
            count = len(list(ROOT.glob("skills/**/SKILL.md")))
            expected = {PACKAGE + ":" + p.parent.name for p in ROOT.glob("skills/**/SKILL.md")}
            actual = {n for n in skills if n.startswith(PACKAGE + ":")}
            assert actual == expected, {"missing": sorted(expected - actual), "extra": sorted(actual - expected)}
        finally:
            process.close()
        process = JsonProcess(["claude", "--print", "--input-format", "stream-json",
            "--output-format", "stream-json", "--verbose", "--setting-sources", "",
            "--settings", '{"disableAllHooks":true}', "--strict-mcp-config",
            "--plugin-dir", str(ours), "--plugin-dir", str(other)], root)
        try:
            response = process.request({"type": "control_request", "request_id": "namespace-check",
                "request": {"subtype": "initialize"}}, lambda r: r.get("type") == "control_response")
            commands = {c["name"] for c in response["response"]["response"]["commands"]}
            expected = {PACKAGE + ":" + p.parent.name for p in ROOT.glob("skills/*/SKILL.md")}
            actual = {n for n in commands if n.startswith(PACKAGE + ":")}
            assert actual == expected, {"missing": sorted(expected - actual), "extra": sorted(actual - expected)}
            for owner in (PACKAGE, "mattpocock-skills"):
                for name in ("pr-review-guide", "find-bugs"):
                    assert owner + ":" + name in commands
        finally:
            process.close()
        print(f"Codex: {count} skills; Claude: {len(expected)} top-level skills. Same-name entry/helper pairs remain qualified; cached helper path and bytes match. No model calls.")


if __name__ == "__main__":
    check_references()
    if "--runtimes" in sys.argv:
        check_runtimes()

"""Check OpenCode discovery without model calls or user configuration changes."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def check():
    subprocess.run(["node", "--input-type=module", "-e", '''
import assert from "node:assert/strict";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const root = process.argv[1];
const { Skills } = await import(pathToFileURL(join(root, "opencode/skills.js")));
const plugin = await Skills();
assert.deepEqual(Object.keys(plugin), ["config"]);
const empty = {};
await plugin.config(empty);
assert.deepEqual(empty, {skills: {paths: [join(root, "skills")]}});
const existing = {skills: {paths: ["/other/skills"]}, permission: {bash: "ask"}};
await plugin.config(existing);
await plugin.config(existing);
assert.deepEqual(existing, {
  skills: {paths: ["/other/skills", join(root, "skills")]},
  permission: {bash: "ask"},
});
''', str(ROOT)], check=True)
    print("OpenCode discovery passed; existing config preserved, no runtime callbacks")


if __name__ == "__main__":
    check()

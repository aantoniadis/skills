# Original skills

Matt Pocock's and HumanLayer's skills that our workflows use. Each user
installs them through the upstream's own route; nothing from them ships in
this package, and each install carries its own MIT license. `setup-tools`
finds the installed copies and records them; other skills read the record.

## Where to look

Check the current host's plugin listing first, then the standard skill
directories, project-local before global. Record one path per skill with
the version the host reports.

- Claude Code: `claude plugin list` names each installed plugin and its
  version. Matt's plugin unpacks to
  `~/.claude/plugins/cache/<marketplace>/mattpocock-skills/<version>/skills/<category>/<name>/SKILL.md`.
- Codex: `codex plugin list` prints each plugin's version and source path;
  the skills sit under `skills/<category>/<name>/SKILL.md` there.
- Standard directories, every host: `.agents/skills/<name>/SKILL.md` in the
  project, then `~/.agents/skills/<name>/SKILL.md`. Hosts link them as
  `~/.claude/skills/<name>`, `~/.codex/skills/<name>`, and
  `~/.config/opencode/skills/<name>`. These copies carry no version: record
  the route and the date you read them.

A listing entry whose `SKILL.md` cannot be read is a gap, not a capability.

## Install commands

When a needed skill is missing, give the user the command for their host and
run it only with their authorization. Matt's README warns against installing
both the plugin and the copied files on one host, which registers every
skill twice.

Matt Pocock's skills:

- Claude Code: `claude plugin install mattpocock-skills@claude-plugins-official`
- Codex: `codex plugin marketplace add mattpocock/skills`, then
  `codex plugin add mattpocock-skills@mattpocock`
- OpenCode and other hosts: `npx skills@latest add mattpocock/skills -g`;
  `-a <agent>` selects the host.

HumanLayer's skills, every host:
`npx skills@latest add humanlayer/skills --skill show-me --skill visual-pr -g`.

## Matt Pocock's skills

Source: https://github.com/mattpocock/skills (MIT). Our workflows use:

| Skill | Kind | Used by | For |
| --- | --- | --- | --- |
| `grilling` | model-invoked | plan-change | a demanding interview on the unresolved choices |
| `to-spec`, `to-tickets` | user-invoked | the handoff from plan-change | the spec and tickets Matt's format publishes to the tracker, synthesized from the planning conversation |
| `implement` | user-invoked on Codex, model-invoked on Claude Code; handed off either way | the handoff from plan-change | implementing an agreed ticket in a fresh session; it calls `tdd` and `code-review` beside it |
| `writing-for-agents` | model-invoked | authoring, see AGENTS.md | writing skill text |

The kind is the author's choice, set in the skill's frontmatter
(`disable-model-invocation: true`), its `agents/openai.yaml`
(`allow_implicit_invocation: false`), or a description that reserves it for
the user. This table records it, so take the kind from here; a user-invoked
skill's files stay unread. [Package references](../../REFERENCES.md) say what
each kind means for our skills.

Any other skill the install brings is usable directly through the host.

## HumanLayer's skills

Source: https://github.com/humanlayer/skills (MIT). Our workflows use:

| Skill | Kind | Used by | For |
| --- | --- | --- | --- |
| `show-me` | user-invoked | the handoff from explain | a visual recap of the finished explanation: component trees, file trees, code-shape diffs |
| `visual-pr` | user-invoked | the handoff from plan-change | creating or updating the PR with its own description template |

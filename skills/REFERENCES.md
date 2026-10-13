# Skill sources and execution

`aantoniadis-skills:<name>` identifies a skill bundled in this package. The
folder and frontmatter name remain `<name>`. Use the host's skill discovery
and invocation tools, or read a local helper's `SKILL.md` directly.

Resolve local helper paths relative to the calling skill's physical directory,
following its installation symlink first. Use the sibling from the same
checkout or plugin cache. If missing, report the package dependency problem.

`mattpocock:<name>` and `humanlayer:<name>` identify the original skill
`<name>` by Matt Pocock or HumanLayer, installed separately and unchanged.
The [original skills](setup-tools/references/upstream-skills.md) table says
which of two kinds each is. The author's gate sets the kind; `implement` is
gated only on Codex, and we hand it off on every host because it starts a
fresh session.

- **Model-invoked** (`grilling`, `writing-for-agents`): invoke it through the host's skill tool
  under the name the host lists, within the caller's scope and authorization.
  Only on a host with no skill tool, read its `SKILL.md` and companion files
  from the path in the [local tool record](TOOL-SETUP.md).
- **User-invoked** (`to-spec`, `to-tickets`, `implement`, `show-me`,
  `visual-pr`): marked `disable-model-invocation: true`, Codex
  `allow_implicit_invocation: false`, or a description that reserves it for
  the user. Only the user runs it, so our skills hand off: finish the current
  deliverable, then give the user the command the host registers, such as
  `/mattpocock-skills:to-spec` or `/to-spec` in Claude Code and the same name
  after `$` in Codex, with the context it needs. Take the kind from the table;
  its files, frontmatter included, stay unread. The host hides its description
  on purpose, and the skill then runs its own workflow, publication included.

A call inside an original to another of its skills, such as `/tdd` inside
`implement`, means the original of that name installed beside it. With no
tool record, look where the original skills reference says and record what
you find. When an original is not installed, give the user the install
command from that reference, then continue with the caller's fallback or
stop the dependent step.

## Execution

Follow the steps in the selected `SKILL.md`, adapting depth to the question.
The host manages progress and subagents.

For useful delegation, see [worker guidance](WORKERS.md). Keep evidence,
source conditions, and unresolved questions with the result. Use the
[local tool record](TOOL-SETUP.md) when choosing capabilities for a project;
its operations are options for the current question.

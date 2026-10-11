# Skill sources and execution

`aantoniadis-skills:<name>` identifies a skill bundled in this package. The
folder and frontmatter name remain `<name>`. Use the host's skill discovery
and invocation tools, or read a local helper's `SKILL.md` directly.

Resolve local helper paths relative to the calling skill's physical directory,
following its installation symlink first. Use the sibling from the same
checkout or plugin cache. If missing, report the package dependency problem.

`mattpocock:<name>` and `humanlayer:<name>` identify the original skill
`<name>` by Matt Pocock or HumanLayer, installed separately and unchanged.
Read the [local tool record](TOOL-SETUP.md) for its path and version; with
no record, look where [original skills](setup-tools/references/upstream-skills.md)
says and record what you find. Read its `SKILL.md` and companion files from
that directory and follow them within the caller's scope and authorization;
direct use follows its own workflow. A call inside an original to another of
its skills, such as `/tdd` inside `implement`, means the original of that
name installed beside it. When an original is not installed, give the user
the install command from that reference, then continue with the caller's
fallback or stop the dependent step.

## Execution

Follow the steps in the selected `SKILL.md`, adapting depth to the question.
The host manages progress and subagents.

For useful delegation, see [worker guidance](WORKERS.md). Keep evidence,
source conditions, and unresolved questions with the result. Use the
[local tool record](TOOL-SETUP.md) when choosing capabilities for a project;
its operations are options for the current question.

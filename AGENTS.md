# Authoring skills

Before creating or editing agent-facing instructions, invoke Matt's original
`writing-for-agents` through the host, as [package references](skills/REFERENCES.md)
say, and apply our [technical-English guide](skills/TECHNICAL-ENGLISH.md). Check that edits
preserve conditions, permissions, obligations, and evidence limits.

## Skill authoring checklist

Sourced from Anthropic's skill best practices, the Claude Code skills
reference, the agentskills.io specification, and Matt's `writing-for-agents`.
Check each before a skill change ships:

- Description: third person; what the skill does and when to use it, in the
  words a user would type; what it is not for when a neighbor overlaps. No
  workflow summary, because an agent may follow the description instead of
  the body.
- Order: the most important instructions near the top of `SKILL.md`. After
  compaction, Claude Code keeps only the first 5,000 tokens of an invoked skill.
- Size: `SKILL.md` under 500 lines; reference files linked one level deep from
  `SKILL.md`; a contents list on a reference file over 100 lines.
- Freedom: exact commands for fragile sequences such as baselines, checkers,
  and renderers; prose for judgment. A deterministic step is a script.
- Claude Code does not re-read a skill after invocation. A rule that must
  hold on every turn is either a host hook or prose phrased for the whole
  task, as in "before every delivery"; this package uses prose.
- One term per concept across all skill files; no dates or versions that go
  stale, except inside a marked example.
- Validate: `claude plugin validate .` and `claude plugin validate skills`,
  the local test suite, and one realistic prompt per trigger branch when a
  description changes.


## Shipping

Bump the version in `package.json`, `.claude-plugin/plugin.json`, and
`.codex-plugin/plugin.json` in the PR; the namespace test fails when they
differ. Run `python3 -m unittest discover -s tests -q` and the two validate
commands; the report fixture test renders a diagram, so run
`npm ci --prefix skills/diagram-renderer` once in a fresh checkout. Every merge
to `main` is a release: tag the merge commit `v<version>`.

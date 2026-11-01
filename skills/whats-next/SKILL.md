---
name: whats-next
description: "Tells the user which skill to run next in the change workflow and how: the step, the command for this host, and whether to stay in this session or start a new one. Use when the user asks what to run next, where they are in the flow, which skill fits the work in front of them, or how to continue after a step finished. Not for doing the step itself (the named skill), preparing tools (setup-tools), or routing among Matt Pocock's skills alone (his ask-matt)."
argument-hint: "Optional: what you just finished, or what you want to achieve"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md); name the evidence
behind the placement, as [evidence](../EVIDENCE.md) says.

# What's next

Give one answer: where the user is in the workflow, the next step, the exact
command, and the session to run it in. Read the state first; ask only when two
positions fit. Write nothing to the project, and stop after the answer: the
user runs the next step.

## 1. Read the state

Run `python3 <package>/skills/whats-next/scripts/workflow_state.py <project>`.
It prints the branch and its distance from the default branch, the uncommitted
files, the investigation location, every note and report our skills left
(understanding note, plan, diagnosis note, PR review guide, acceptance report)
with its summary line and date, local tickets, `visual-pr` tasks, Matt's
tracker setup, and whether a local tool record exists. It reads only and
creates nothing.

Add what the scan cannot see: the step this conversation just finished and the
path or URL it reported, the decisions the user stated, and the argument when
it names a goal. When the branch has an upstream, check for an open PR with the
host's Git tooling, such as `gh pr view`. Print the tool record with
`python3 <package>/skills/tool_setup_path.py --show <project>` to learn which
originals are installed and how the host registers them; `none` means no setup
ran, so take install commands from
[original skills](../setup-tools/references/upstream-skills.md).

## 2. Place the user

Take the first row whose evidence holds, top to bottom. "The same session"
is the one that holds the planning conversation. "A new session" is a fresh
context window: a new session in the host, or its clear command.

| Evidence | Next | Session |
| --- | --- | --- |
| A failing check, an issue reporting wrong behavior, or a production symptom, with no diagnosis note for it | `fix-bug`, with the symptom and the contract when known | Where the symptom arrives: the implementing session for a check it broke, a new one for an issue or a production symptom |
| A PR the user did not write and has to review | `pr-review-guide`, with the PR URL | A new session, without the author's context |
| An epic, tickets, or a spec, and a delivered head or an integration branch | `check-acceptance`, with the sources and the head | A new session on the delivered head |
| An acceptance report with Partial or Unmet rows, or bug cards | `plan-change` for a missing decision, Matt's `implement` per gap, `fix-bug` per bug card, each with the report path | A new session per handoff |
| A feature branch ahead of the default branch, and no PR | `find-bugs` on the branch against the default branch, then HumanLayer's `visual-pr` | The implementing session, or a new one checked out on the branch |
| Tickets with blocking edges, and no commits for them yet | Matt's `implement` per unblocked ticket, or `implement-spec` for the whole spec | A new session per ticket, on the feature branch; one new session for `implement-spec` |
| A plan whose Readiness line says ready, and no spec or tickets | `plan-change` to draft the spec and tickets, or Matt's `to-spec` then `to-tickets` | The same planning session, unbroken |
| A plan with open decisions or blocked slices | `plan-change` on the open choices | The same planning session |
| An understanding note, and no plan | `plan-change`, with the note path | The same session |
| A change with consequences beyond its own function, and no note or plan | `explain` for one concrete question about today's behavior, or `plan-change` when the flow is already known | Start the planning session here |
| A contained change in familiar code | No skill: the host's normal coding workflow, with `find-bugs` when a defect search would help | The current session |
| Investigation work ahead, and no local tool record | `setup-tools`, naming the skills to run | Any |

An idea with no repository under it takes Matt's `grill-me`. A huge, foggy
effort takes his `wayfinder`, which merges at `to-spec`. When two rows fit and
the conversation does not settle it, ask one question with the recommended row
first, as [asking](../ASKING.md) says for a round and for a host without the
question tool.

## 3. Answer

Reply in this shape, with the real paths and URLs from the scan:

```text
**Where you are:** <position, with its evidence: branch, file, PR, report line>
**Next:** <skill> — <what it settles, one line>
**Run:** <the command for this host, with the paths and the choices already settled>
**Session:** <same | new> — <reason>
**Carry:** <the paths or URLs the next step needs, which a fresh session cannot see>
**Also possible:** <one alternative row, and when it is the better one>
```

Write the command as the host registers it: `/aantoniadis-skills:<name>` in
Claude Code, `$aantoniadis-skills:<name>` in Codex, `/<name>` or
`opencode run --command <name>` in OpenCode; an original as the tool record
lists it, such as `/mattpocock-skills:implement` or `/implement`. Put a
kickoff choice the conversation already settled inside the command, so the
next skill asks less. When an original is not installed, give its install
command and the local route instead. Name what was not checked, such as a
tracker that could not be reached. Done when the user can paste the command.

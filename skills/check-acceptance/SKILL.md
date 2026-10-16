---
name: check-acceptance
description: Checks delivered code against a set of requirements — GitHub issues, an epic, Jira or Linear tickets, a spec or plan, or pasted text — and reports which are met, partly met, unmet, unverified, or unclear, with evidence; also delivered behavior nobody asked for, and a search for bugs when selected. Use when the user asks whether issues or an epic are done, wants an acceptance or requirements check before closing tickets or releasing, or asks what is missing or implemented wrong. Not for one PR's review guide (pr-review-guide), comparing one diff with its spec (code-review), defects in a diff alone (find-bugs), or deciding intended behavior (plan-change).
argument-hint: "<issues, epic, tickets, spec, or text; revision to check and base if known>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Check acceptance

Tell the person who accepts delivered work, for each requirement, whether the code at one pinned revision meets it, with evidence. Also report delivered behavior in the feature's code that no requirement asked for and, when selected, defects in that code. Maintain one current Markdown report and, when requested, its self-contained HTML companion, written in the shape of [report-format.md](references/report-format.md), starting from [report-template.md](references/report-template.md).

The check is read-only: it changes no application code, tests, or ticket state, and it never closes, labels, or reopens a ticket. The report gives counts and blockers, not a merge or ship verdict; the ship decision is the user's.

## 1. Kickoff and pin

Hold the kickoff round from [asking](../ASKING.md) first, with the questions the request leaves open: how much codebase familiarity to assume; the deliverable, text (recommended) or text plus an HTML companion; whether to confirm the extracted requirement list before verification (recommended) or run straight through; and *Search for bugs?*, *Yes* (recommended) or *No*. Apply a choice the request states without asking. The confirm question is an exception to the [asking](../ASKING.md) rule that "go" applies the recommendations: "go", no answer, or a non-interactive session runs straight through. The first delivery states every applied choice in its `Kickoff:` line.

Pin `head` as a full SHA: the checkout's HEAD, or a named branch resolved to its SHA. A `base` is optional and serves attribution only. When a base is inferable, such as the merge-base of a feature branch with the default branch, find it and state it as an assumption instead of asking. Write `head`, `base` when pinned, and `repository: owner/name` in the report's front matter. Record local modifications and relevant configuration; dirty source follows the [snapshot rule](../EVIDENCE.md#capture-a-local-snapshot).

Create `report.md` at the location the caller supplied, else the routine location from [asking](../ASKING.md), with the review record `review.md` beside it and tool outputs and probes under `runs/`. The review record holds one run record per check, failed and blocked checks included, with its command, conditions, result, and limits, and each consequential correction with the prior claim, its replacement, the reason, and the evidence. Read the [local tool record](../TOOL-SETUP.md) if present.

Collect the intent sources: GitHub issues and epics through `gh` (body, comments, sub-issues, linked PRs); Jira or Linear tickets through the host's MCP connector when connected; URLs; local files; a [plan-change](../plan-change/SKILL.md) plan, whose acceptance outcomes map one-to-one to requirements; pasted text. Record each source's collection time, because issues change. Name an inaccessible source as a gap.

Done when the `Kickoff:` line is ready, `head` is a full SHA, the base is pinned, assumed with its reason, or recorded as absent, and every source is collected with its time or named as a gap.

## 2. Extract requirements

- Atomize each source into rows of one observable condition each, quoted and linked to the specific source: the issue, comment, ticket field, or plan heading.
- Keep explicit acceptance criteria separate from requirements inferred from description prose, and label inferred ones *inferred*.
- Deduplicate across sources; keep every source link on the merged row.
- When a later comment revises the body, quote both. The **spec owner** is the person who owns the intent source, such as the issue author or the ticket's reporter. The spec owner's latest comment that states a new value or wording supersedes the body, as in "actually the header should be `Y`"; check the row against it. A revision by anyone other than the spec owner, or one phrased as a question or a suggestion, as in "does the header need `status`?" or "maybe add `status`", leaves the row **Needs clarification**.
- A vague non-functional requirement, such as "fast" or "secure", is **Needs clarification**, with a measurable reading proposed and labeled *inferred*.

When the user explicitly chose to confirm, show the list with each quote, source, reading, and flagged conflict, and stop once. The rows under *Requirements* are the list, and its `**Requirement list:**` line says whether the user confirmed it, as [report-format.md](references/report-format.md#requirements) describes.

Done when every reachable source is atomized into quoted, linked rows, and the user has seen the list when they explicitly chose to confirm it.

## 3. Scope the feature code

The **feature scope** is the code that implements the requirements: the linked diffs plus the traced code. Seeds start it and tracing completes it; the base..head range is never the scope.

- **Seeds:** PRs and commits linked to the sources: GitHub development links, `Fixes #N` or `Closes #N`, and ticket keys in commit messages or branch names (`git log --grep`).
- **Trace:** for each requirement, follow its entry point (route, CLI command, UI, public API, job, or configuration) to its observable outcome. The trace finds implementing code that the links missed.
- **Record** the feature scope under *Feature scope* in the report, with the linked PRs and commits and the traced entry points.
- **Unrelated commits** in base..head stay out of the scope. One that touches traced code is an **interaction lead**: check whether it changed the requirement's outcome.

Attribution runs only with a base, and only for Unmet and Partial rows; a Met row needs none, and bug cards take their origin from find-bugs. It answers a behavior question, not a blame question:

- "Already existed" means the same requirement check gives the same result at the base: the same source reading at the base, or the same probe run there.
- `git blame` is a lead only. Run `git blame -w -M -C`, with `--ignore-revs-file .git-blame-ignore-revs` when that file exists, and map a squash-merge commit to its PR.
- When linked commits or PRs and blame disagree, the linked work wins. Unresolved attribution is `unknown`. Attribution never changes a row's status.

Done when every requirement has a traced entry point or a named gap, and the feature scope, interaction leads, and attribution method are recorded.

## 4. Verify each requirement

The **Met bar:** a structural requirement can be Met from pinned source. A behavioral requirement needs an asserting test plus a recorded run (CI at the pinned head, or a run here), or a focused probe. Source tracing alone gives **Not verified**, with the settling check named.

- Use these statuses: Met, Partial, Unmet, Not verified, Needs clarification, Not applicable. `--sync-labels` writes their key into the report.
- Read relevant tests for what their assertions establish under their setup and mocks. Names and passing counts cannot clear an unexercised scenario.
- A recorded CI run at the pinned head is the suite result; cite it with its conditions. Run only the focused check or probe that a named gap needs. Choose checks, and recover from failed tools, as [CODE-TOOLS.md](../CODE-TOOLS.md) says.
- **Unmet** needs positive evidence: behavior that contradicts the requirement, or absence after tracing every named entry point. An absence claim names the paths and configurations inspected, as the [negative-claim rule](../EVIDENCE.md#identify-the-evidence) requires.
- **Not applicable** needs a recorded, agreed scope decision that excludes the requirement; link that decision and give the reason.
- **Partial** applies when some named entry points or conditions hold and others fail. It names the ones that hold and the remainder, and it still names each failing one.

For a large source set, use an [investigator](../INVESTIGATE.md) per source or requirement group through [native delegation](../WORKERS.md), framing the scenario to trace, not a suspicion to confirm.

Done when every row's status meets the Met bar, and its evidence cell links pinned source, a run record, or a bug card, or names the gap.

## 5. Find delivered behavior nobody asked for

Under *Nobody asked for this*, list delivered behavior inside the feature scope that no intent source supports, with the `intent-alignment` label *nobody asked for this*. A necessary implementation detail is not scope creep.

Done when the section lists each such behavior with its pinned source, or states `None found:` with the scope inspected.

## 6. Search for bugs

When selected, load [find-bugs](../find-bugs/SKILL.md) and follow it as a scoped helper, yourself or through native delegation. Supply the head, the base when pinned, the feature scope (commit set and traced files or symbols), the report directory, the local tool record when available, and hypotheses from the verification step. Keep its probe scripts, fixtures, logs, and environment records under the report directory's `runs/bugs/`. Integrate returned defects as bug cards with the [acceptance origins](references/report-format.md#bug-origins):

- A bug that breaks a requirement sets that row to Partial or Unmet and links its card.
- Every other bug gets its own card.

When the user skips the search, write `The search for bugs has not run: you chose to skip it.` as *Possible bugs*.

Done when every returned defect has a card and its requirement row is updated, or *Possible bugs* holds the none-found or not-run paragraph.

## 7. Check and deliver

Compare the bottom line, attention items, rows, bug cards, and questions with their evidence; use a [second reader](../FRESH-REVIEW.md) when useful. Before every delivery, after the last edit, run `python3 <package>/skills/render_page.py <report.md> --check --acceptance --sync-labels`, including for text-only reports, with `--repo <checkout>` when the report sits outside the checkout. Learn its rules from its messages: write the report, run the check, fix what each message names, and rerun before presenting the report as complete. For HTML delivery, read and apply the [shared page workflow](../HTML-PAGES.md) with the page notes of report-format.md.

Reply with the absolute report link, counts by status, and the top gaps. Then hand off gaps and Unmet rows to `/aantoniadis-skills:plan-change` or to `mattpocock:implement` as [package references](../REFERENCES.md) say, and bugs to `/aantoniadis-skills:fix-bug` (`$` instead of `/` in Codex). Each command carries the report path and the rows it concerns. Send Needs clarification rows to the spec owner as questions.

When the user requests it, draft one comment per issue or ticket with its rows, statuses, evidence links, and the pinned head. Post only within authorization, as [asking](../ASKING.md) describes, and record each posted URL in the review record.

Done when the checker passes after the last edit, or the report is labeled structurally unchecked with the blocker, and the reply carries the link, counts, gaps, and handoff commands.

## 8. Re-check, do not restart

A follow-up, such as "re-check after the fixes", resumes the same report and review record. Collect the intent sources again and compare them with the report's quotes and collection times: an edited body, a new comment, or a changed sub-issue reopens the rows that source feeds, under the step 2 rules, and adds any row it newly asks for. When the head moved, list the arrived commits, split into feature-relevant ones (touching the feature scope or linked to a source) and unrelated ones, and offer to re-pin. A re-pin reopens only rows whose traced code, linked work, or evidence changed; restate the `**Requirement list:**` line when rows were added; record what was rechecked, each new collection time, and what still refers to the earlier head. Run the check in step 7 after the last edit.

Done when every source has a current collection time or is named as a gap, every reopened row has a current status and evidence, and the report passes the check against the head in force.

---
name: find-bugs
description: Finds the defects in a change (a PR, a branch, or the working tree) that a maintainer would fix, with evidence from inspected source or executed probes. Use when the user asks to find bugs, review a diff for defects, or check a change before it merges or before a human reviews it; pr-review-guide and check-acceptance call it for their search for bugs. Not for explaining how code works (explain), planning a change (plan-change), or writing the human reviewer's guide (pr-review-guide).
argument-hint: "<PR URL or number, branch, or 'the working tree'; anything the finder should know>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Find bugs

Return defects a maintainer would fix, with their trigger, consequence, and supporting evidence. Keep speculative possibilities out of the finding list unless source or observations support a plausible in-scope trigger and material impact. A probe establishes an observation; the contract and the consequence decide whether it is a defect.

## 1. Pin the scope

Record the repository root, head SHA and comparison base for a PR, or head and merge-base for a branch. State relevant dependency and deployment conditions. Reuse the caller's pins and agreed requirements. A caller can supply a **feature scope** in place of a diff: a head plus a commit set or traced files and symbols, with an optional base; read that scope as the changed source. Without a base, probes observe the head only, and every finding's origin is **no base pinned**. Ask only when missing scope or intent changes the result.

For a working-tree review, state whether the comparison includes staged, unstaged, and untracked files. Retain the selected diff and [capture the inspected files](../EVIDENCE.md#capture-a-local-snapshot); a commit link does not support dirty bytes. Recheck affected findings if the source changes during investigation; report the snapshot actually reviewed.

Read changed source within the selected scope and trace consequential callers and consumers. Record generated, binary, unavailable, or excluded material and how it limits the review. Follow concurrency and lifecycle boundaries when the change involves shared state, cancellation, streaming, cleanup, or similar risks. Use a separate perspective through [native delegation](../WORKERS.md) when useful.

Done when the compared revisions, the included working-tree state, and excluded material are recorded, and the changed source in scope has been read.

## 2. Generate and investigate candidates

Read every changed line with one question: under what input, version, timing, or caller does it misbehave? Tools add leads; the reading finds the rest. Choose tools using [CODE-TOOLS.md](../CODE-TOOLS.md) and any [local tool record](../TOOL-SETUP.md). Tool results are leads, not defects. Reuse results only when their revisions, inputs, environment, and scope match. Selected tools should answer a useful question; missing optional setup does not stop source investigation.

Useful leads include:

- **Coverage gaps:** project coverage results at the inspected source. For two committed revisions, [`untested_added_lines.py`](scripts/untested_added_lines.py) compares added source lines with coverage.py or Istanbul/Vitest JSON. It distinguishes executed, missing, excluded, and unclassified data; statement-start coverage does not establish branch or input coverage. Run with `--base <base> --head <head> --repo <checkout> --cov <report>`. The caller verifies report provenance. For dirty or untracked source, use matching project coverage and the retained snapshot; the commit comparison helper does not cover it.
- **Dependency compatibility:** use the project's supported-version tests, constraints, or resolver in a fresh environment when changed ranges or new dependency API calls raise a question. Honor the selected Python/runtime, environment markers, extras, and full constraints. Verify installed versions and run a focused operation. A failed install leaves an evidence gap. Preserve existing environments and logs.
- **Second consumers:** inspect existing callers of a function newly called or copied by the change. Compare outputs, cleanup, and signals those callers use with what the new consumer handles.
- **Static deltas:** compare relevant type-checker and linter diagnostics at base and head under comparable configuration. Retain actionable findings and deduplicate overlapping diagnostics. A diagnostic is evidence of what the tool reported; it does not by itself demonstrate the predicted runtime consequence.
- **History and review context:** use blame, focused history searches, and issue/PR tools to resolve a named uncertainty. Keep history tied to the inspected revision. Retrieve relevant comment pages or state the partial scope; a later fix is a lead, not evidence of behavior at the selected head.
- **Caller hypotheses:** investigate supplied line, condition, and predicted-result hypotheses. Search additional paths when the available results do not answer the question.

For each material suspicion, state the line, triggering conditions, predicted observable result, and the requirement or contract it would violate. Read controlling guards, relevant consumers, and counterevidence before investing in a probe. Stop a tool investigation when it answers the named question or leaves an explicit gap.

Done when each material suspicion states its line, trigger, predicted result, and violated contract, or is dropped with its counterevidence.

## 3. Probe and retain evidence

Use the cheapest adequate check through the relevant public boundary: a focused existing test, small script, or request through the changed path. Ordinary authorized local checks can proceed. Ask before material unapproved cost, side effects, or scope expansion; continue independent investigation while waiting. Application fixes and publication require their own task scope.

Verify that the probe loads the intended checkout and dependencies. Compare base and head under equivalent relevant inputs and environments; record differences and their limits. If the base cannot run, label its result as a prediction. A model or instrumented run establishes only what it exercises. Instrumentation can expose a real defect; determine whether it observes the failure or introduces a condition outside supported use.

For standalone work, keep useful scripts, inputs, commands, output, and environment details at the investigation location from [asking](../ASKING.md). With a caller's report directory, save probe scripts, fixtures, logs, and environment records under `runs/bugs/`; tool results can go under `runs/tools/`. Use fresh disposable environments or worktrees when needed, within the caller's tool scope. Preserve the caller's report and leave presentation and publication to it.

For an executed finding returned to a caller, save the probe script before running it so the saved file is the one that ran. A short wrapper can invoke an existing test. Retain the result and exact command, not only the script. Classify each investigated hypothesis as supported, contradicted with counterevidence, or unresolved with the missing check. Record useful drops compactly in notes rather than making the reader inspect every abandoned lead.

Done when each hypothesis is supported by a saved probe, contradicted with counterevidence, or unresolved with its missing check.

## 4. Check, rank, and deliver

For each candidate, check reachability, the applicable contract, actual or predicted consequence, and origin. Drop an unchanged pre-existing defect from the change's defect list unless broader review was requested. That drop needs a base: without one, keep every defect in the feature scope, labeled **no base pinned**. Label a defect in the feature scope **from an unrelated commit** only when evidence, a bisect or the caller's commit set against blame, names an introducing commit outside that commit set, and name the commit; blame alone is a lead. Keep a pre-existing defect when the change makes its result worse or exposes it through a new path, labeled **made worse**. A similar pattern elsewhere does not exonerate a new defect.

Compare intent with agreed requirements and applicable contracts. A test or documentation line can explain intended behavior; it does not alone establish that the behavior satisfies the requirement. Reuse settled intent. Ask the author only for missing intent or facts they must supply that affect the finding. An untested configuration or hypothetical unreachable path alone does not warrant a question or defect. Bound a negative probe to the configuration it exercised, and retain other configurations only when evidence supports a material concern.

Keep actionable lint/type errors and valid instrumented observations. Drop a hypothesis when a controlling line or observation contradicts it; an assumption about deployment, threads, or timing is not counterevidence. State consequential unresolved assumptions and a check that would settle them. Compare the final claims with their sources before delivery.

Rank by impact, reach and likelihood, recoverability, and confidence. Explain the affected consumer's next action. Silent errors, loud failures, and rare configurations have no fixed priority independent of their consequence.

Deliver `## Defects`, with a numbered item per finding: pinned location, trigger, consequence, origin, evidence status, and consumer impact. Use **executed** for the stated observation with its command/output; use **inferred** for a source-supported prediction and the missing probe. If no defect is found, say so within the inspected scope and name what was checked and the remaining gaps. Include `## Questions for the author` for material unresolved questions, or state that none remain. Keep routine drops and detailed tool logs in the investigation notes.

When [pr-review-guide](../pr-review-guide/SKILL.md) or [check-acceptance](../check-acceptance/SKILL.md) calls this skill, provide the fields its [bug cards](../pr-review-guide/references/report-format.md#bug-cards) need: origin as new, made worse, from an unrelated commit with the introducing commit's SHA, or no base pinned; separate base/head results; and `predicted:` for each unobserved result. For an executed finding, include the exact command, decisive output excerpt, and script path relative to the report such as `runs/bugs/duplicate-event.py`. For an inferred finding, include separate base/head predictions and a runnable settling check. The caller owns integration.

Done when findings have actionable triggers and consequences, evidence matches the stated confidence and source, and material limits are visible. Finding no defect is a scoped result, not proof that the change is correct.

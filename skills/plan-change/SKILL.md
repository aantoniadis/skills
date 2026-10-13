---
name: plan-change
description: Plans an engineering change, or reviews an existing plan, for indirect behavior changes and consequential assumptions, and drafts specs and tickets when selected. Use when a ticket or request is vague, when a change has consequences beyond its own function, when the user asks what must be decided before implementing, or when a plan needs review. Not for explaining how code works today (explain) or reviewing a finished diff (find-bugs, pr-review-guide).
argument-hint: "<ticket, request, or plan to review; the understanding note to reuse if any>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md): observed behavior, source-supported
inference, agreed intent, proposal, or unknown.

# Plan change

Produce a plan another engineer can implement without inventing consequential behavior. Resolve missing behavior decisions, overlooked workflows, and consequential factual assumptions within the agreed scope. Leave routine coding choices to implementation.

## 1. Establish context

Identify who needs the change, their workflow and outcome, scope, and behavior to preserve. Reuse existing answers. Ask only when missing intent changes the recommendation. A ticket's proposed interface is a candidate unless already required.

Hold the kickoff round from [asking](../ASKING.md) first, with the questions the request leaves open: the deliverable, a plan, a spec, or tickets (recommend the plan first); an HTML companion or text only (recommend text); and whether the user decides each consequential choice or authorizes an autopilot policy (recommend deciding each). Apply a choice the request states without asking; a review of an existing plan keeps its deliverable. The first delivery states the applied choices in its `Kickoff:` line.

Use one authoritative plan: an existing designated plan/spec/ticket, else the location from [asking](../ASKING.md). For a new plan, adapt [plan-template.md](references/plan-template.md); remove unused sections. Before delivering, run `python3 <package>/skills/render_page.py <plan.md> --check --sync-labels --markdown-only` for text, and without `--markdown-only` for HTML; it checks the plan and writes the label key when the plan uses status tables or diagrams. Default to a text plan unless the user requests another deliverable. Carry forward any decision policy, including explicitly authorized autopilot; ask about unresolved consequential choices outside that policy.

For a review request, inspect the existing plan and report findings before rewriting it. When revisions are requested, update the authoritative plan in place. Retain settled decisions and valid evidence; reopen only what new findings or changed scope affect. Check relevant source changes, local modifications, configuration, and dependencies.

Before investigating, use [CODE-TOOLS.md](../CODE-TOOLS.md) to select useful capabilities and reuse local preparation. Use an [investigator](../INVESTIGATE.md) through [native delegation](../WORKERS.md) for a separate factual gap when useful. Pass the question, source conditions, existing evidence, and authorization.

## 2. Investigate and decide

Repeat this loop while material choices or assumptions remain unresolved:

1. **Compare behavior.** Apply [behavior comparison](../BEHAVIOR-COMPARISON.md) to the same scenario today and under the candidate, through the affected consumer's next action. Select consequential scenarios and interactions from the inspected flow. Use a matrix when combinations help explain a risk; record evidence and untested gaps without requiring every possible combination.
2. **Check preservation and uncertainty.** Identify changed and preserved behavior. Reuse valid source evidence and run focused checks where they resolve a consequential uncertainty. Label candidate experiments with the unagreed choices they assume; results remain conditional on those choices. A preservation conflict needs alternatives and a decision. Ordinary authorized local checks can proceed. Ask before material unapproved cost, side effects, or scope expansion; continue independent work while waiting.
3. **Resolve the tradeoff.** Explain current → proposed behavior, who notices, their next action, viable options, and a recommendation. Ask a manageable group of questions whose prerequisites are settled. Investigate facts yourself; the user or their authorized policy chooses intent. A "go" settles the choices presented, not unnamed later choices; what counts as agreement follows [asking](../ASKING.md).
4. **Record the decision.** Use a stable descriptive name and status. Capture the scenario, intended and preserved behavior, reason, supporting evidence and limits, accepted risks, and authority. Acceptance states starting condition + action → observable outcome and consumer response. Connect it to the delivery slice. Record policy-based decisions as such, separately from individual answers.

For a difficult interview, optionally invoke `mattpocock:grilling` as [package references](../REFERENCES.md) say, scoped to the unresolved choices and the existing decision policy; if unavailable, report that and continue the loop above.

When evidence changes a decision, record what changed and why, reopen the affected choice, and reconcile downstream artifacts after agreement. Production implementation is a separate task; comparison experiments do not authorize it.

## 3. Retain useful evidence

Keep decisions, blockers, and material revisions in the authoritative plan. A short change note usually suffices. Use separate history and milestone snapshots when the change spans substantial revisions or handoffs, or the user requests them; committed Git history can serve this purpose. Preserve prior agreements and experiment records that explain a changed conclusion. Label reconstructed history and missing versions honestly.

Record the inspected repository root, revision, relevant configuration, and local changes from the source directory, which can differ from the workspace. For retained evidence from dirty or non-Git source, [capture a local snapshot](../EVIDENCE.md#capture-a-local-snapshot) and link it relative to the plan; a revision plus "modified" cannot identify the observed source. Preserve working evidence links when moving or copying artifacts.

Record measurements only when relevant and actually available, with their scope. Keep audit facts, not an interview transcript or reasoning trace.

## 4. Check readiness

Rehearse one consequential decision through the consumer's next action, evidence, delivery slice, and acceptance outcome. Then check every in-scope decision:

- Intended behavior and relevant preservation requirements are settled, including how consumers recognize and respond to the result.
- Consequential factual assumptions have evidence or an explicitly accepted named risk. Accepting risk does not choose the intended behavior.
- A named slice and concrete acceptance outcomes carry the decision. The implementer can determine what should happen without inventing its meaning.

Connect acceptance, delivery, and authority, including decisions outside the summary table. Link blockers to affected slices and slices to controlling code/interfaces, dependencies, and checks at existing public seams. Reuse agreed test seams. Rehearse intermediate states, compatibility, partial failure, recovery, and irreversible rollout steps where relevant. Resolve missing consequential choices through the same loop.

Deliver useful partial work with affected slices marked blocked. Planned implementation tests alone do not make a settled plan unready. When independent review is requested or warrants its cost, use [review-and-feedback.md](references/review-and-feedback.md); it is optional and cannot create agreement or prove runtime behavior.

## 5. Present and hand off

Compare claims with their evidence before delivery. Lead with outcome, scope, readiness, consequential blockers, agreed changes, and preserved behavior. Include before/after scenarios, delivery slices, and verification still needed. In chat, summarize decisions or blockers needing attention and link the plan with a short account of what changed.

For a useful or requested HTML companion, follow the [shared page workflow](../HTML-PAGES.md) and [planning-page guidance](references/planning-page.md). The plan is the source of findings.

### Specs and tickets

When the user selects a spec or tickets:

1. **Choose the route.** Matt's `to-spec` and `to-tickets` are user-invoked: they synthesize a spec or tickets from the conversation so far and publish them under their own workflow. When the user wants that format and publication, hand off to `mattpocock:to-spec` or `mattpocock:to-tickets` as [package references](../REFERENCES.md) say: deliver the plan, then give the user the command with the plan path, and stop; steps 2 to 4 then belong to the original. If it is not installed, give the install command instead of a local draft. Otherwise draft directly using the requirements below, from the existing decisions and agreed test seams. This task excludes tracker setup, project instruction edits, and implementation.
2. **Carry the agreement.** A spec states outcome, scope, named decisions, changed/preserved behavior, acceptance, evidence limits, risks, blockers, and delivery slices. Each ticket contains its own What to build, acceptance and preservation outcomes, Blocked by, and Status, plus decision references, relevant evidence, and a feedback destination. Use vertical slices where practical; state necessary sequencing and intermediate behavior. Links alone cannot carry acceptance criteria.
3. **Check meaning and coverage.** Check each material factual claim and acceptance criterion against the plan and evidence. Paraphrases are valid when they preserve meaning and qualifications. Label unsupported intent as proposed and unsupported facts as unknown; remove irrelevant claims. Cover every agreed decision in the spec and affected tickets. An event count does not establish consumer behavior; an accepted risk is not a measured outcome.
4. **Deliver or publish within scope.** Show the drafts, material unresolved choices, evidence gaps, and readiness of affected slices. Use [publication guidance](../ASKING.md): act within existing authorization, or show concrete drafts and ask for missing authorization. Readiness and permission are separate; a tool failure revokes neither user intent nor existing permission. Keep consequentially blocked work labeled blocked. Apply the tracker's ready label (Matt's `ready-for-agent`) only to work meeting the readiness criteria. Before a remote handoff, include essential evidence in the artifact or link references its readers can access; a local scratch path alone is insufficient.

After a reviewed spec becomes authoritative, point the earlier plan to it and link the tickets. If a tracker comment is useful within the requested task, prepare a concise decision/evidence summary and publish only within authorization. Record published URLs with the plan. Upstream originals remain unchanged; direct invocation follows their original workflows.

Include feedback instructions in the handoff: record expected → discovered behavior, evidence, affected decision/slice, and needed clarification or rework at an accessible destination. Reopen new consequential choices before dependent implementation; independent work can continue. When feedback arrives, use [review-and-feedback.md](references/review-and-feedback.md) to distinguish planning omissions, incorrect assumptions, accepted risks, and later changes.

Implementation and PR creation remain separate tasks that the user starts. For implementation, hand off to `mattpocock:implement` as [package references](../REFERENCES.md) say, with the ticket and accessible evidence in the command for a fresh session. For the PR, hand off to `humanlayer:visual-pr` the same way, with delivered intent, decision references, and actual verification as its task. Planning finishes with self-contained inputs; it does not wait for implementation.

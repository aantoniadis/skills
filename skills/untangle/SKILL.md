---
name: untangle
description: Maps how an existing component really works, finds one rule's logic scattered across modules and layers, capabilities nobody documented, and guards or fallbacks nobody can justify, and proposes a rework that gives each rule one owner. Use when existing code has become hard to follow or change, when the user asks to de-slop, clean up, untangle, or restructure a component, to map the architecture as it is today, or to compare the code with its documented design. Not for explaining one flow (explain), planning a behavior change (plan-change), or finding defects in a diff (find-bugs).
argument-hint: "<component, directory, or flow to untangle; what hurts about it, if you know>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Untangle

Produce the **rework map** of one component: what it does, how it is built today, where that differs from what people believe, and a rework the user can choose. In the target, every rule and every piece of state has one **owner**: the module that decides the rule or writes the state. Application code and tests stay as they are; probes and scratch copies live in the investigation location.

Three rules hold for the whole task:

- **Relationships come from tools and runs.** Record a call, a dependency, or "this input reaches that line" from a resolver, a search result, or an execution, and keep the command. Names, groupings, and explanations are yours to write. A relationship taken from a comment, a name, or your reading alone carries the label *inferred*.
- **The user supplies intent; you supply facts.** Answer every question the code, its history, or a run can answer. Ask the user what only a person knows: why something exists, whether a behavior is intended, which flows matter, and which design they want. Write each answer into the map, so a later session reads it instead of asking again.
- **What nobody can explain stays.** A guard, fallback, or branch whose reason is unknown is kept and listed as a question. A removal is proposed only on the evidence [special cases](references/special-cases.md) requires.

Steps 2 to 4 describe the component. Judgment starts at step 5, so the user corrects a description before reading an argument built on it.

## 1. Agree the scope and establish what runs

Hold the kickoff round from [asking](../ASKING.md) first, with the questions the request leaves open: the scope, one component or flow with a proposed starting path (when the user names none, recommend the place where change is paid most, from the most changed files that [`change_coupling.py`](scripts/change_coupling.py) prints); the deliverable, the map alone or the map with a rework proposal (recommend the proposal); an HTML companion or text only (recommend HTML when the scope has more than one flow); and how to work together, a checkpoint after steps 2, 4, and 6 (recommend it) or a guided walk through the code, where you step through one flow with excerpts and run results and the user directs the depth, following the trace loop of [explain](../explain/SKILL.md) as a helper run.

Then establish the ground, using [CODE-TOOLS.md](../CODE-TOOLS.md) to select capabilities and reuse local preparation:

- Record the repository root, revision, local changes, and configuration from the source directory.
- Run the scope's test suite once and keep the command, result, duration, and coverage command under `runs/` at the investigation location, which `python3 <package>/skills/investigation_dir.py <topic> <project>` creates and prints. This run is the baseline every later probe is compared with.
- Check the history: `git rev-parse --is-shallow-repository`. Deepen a shallow clone within existing authorization, or state the number of commits every history count rests on.

When the scope cannot run here, try the repair route of [setup-tools](../setup-tools/SKILL.md). If it still cannot run, say so at the top of the map: every claim is then read at the line, no special case gets a reach probe, and the map proposes no removal.

Done when the scope is a named set of paths, the revision is recorded, and the baseline has a recorded result or a named obstruction.

## 2. Record the stated design

Work from the outside in, before reading internals: the structure you find is evidence, and the stated design is what it is measured against.

- **Capabilities.** List what the component does for its consumers, in the project's own domain words, from its entry points (routes, commands, exported functions, jobs, event handlers), its callers, its documentation, and its test names. A test name states intent; the code under it establishes behavior.
- **Stated design.** Collect the components the documentation, decision records, instruction files, and directory layout name, and the dependencies allowed between them. Quote each stated rule with its link, such as "the server gates every write". When nothing states a design, write the one the entry points and layout imply, label it *inferred*, and make it the first thing the user corrects.

Checkpoint: show the capability list and the stated design. Ask what is missing or wrong, which flows matter most, where the code hurts, and which oddities are deliberate, such as a guard added after an incident.

Done when every entry point in scope belongs to a capability or is listed as unassigned, and every stated component and allowed dependency has its source: a quote, the user's answer, or *inferred*.

## 3. Take a census of each capability

A **decision site** is a place that decides something about a capability: a condition, a default, a validation, a transformation, or a write to its state. The **census** of a capability is every decision site, wherever it lives: helpers, validators, serializers, middleware, configuration, queries, templates. Take it as [census](references/census.md) says, from four kinds of evidence (text, references, execution, history), and read where they disagree: code a scenario executes that no search for the capability's words found is a hidden part of it; code those words find that no scenario executes is a lead to dead code; files that change together with no dependency between them are a lead to one rule kept in two places.

In the same pass, list the scope's special cases with [`special_cases.py`](scripts/special_cases.py) and your own reading. A **special case** is code that exists for one situation: a guard, a default, a swallowed error, a retry, a compatibility path, a parameter one caller sets.

A **lead** is where to look. It enters the map only after you have read the code on both sides and, where a run decides it, run it.

Take the capabilities in the user's order of importance. For a large scope, give each capability to one [investigator](../INVESTIGATE.md) through [native delegation](../WORKERS.md), with the stated design, the baseline, and the census reference; the map is the shared record. Split the work by capability, because a split by layer hides exactly the scattering this step looks for.

Done when every capability either has its decision sites listed with pinned lines and the kinds of evidence that found each, or is listed as *not inspected* with the reason; every main flow has a recorded run or a named obstruction; and every lead is confirmed, refuted, or listed as open.

## 4. Draw the map as it is, and compare

Draw three views, each from extracted facts:

- **Dependencies.** Get the edges between the scope's files from the ecosystem's resolver, or from [`import_edges.py`](scripts/import_edges.py) as a floor. Write the stated design as the JSON that [`design_conformance.py`](scripts/design_conformance.py) reads, and run it: every relationship comes out *as stated*, *not stated* (the code has it and the design does not allow it), or *not found* (the design names it and no edge shows it). Read the file edges behind each result that is not *as stated*.
- **State.** For each piece of state the scope keeps (a table, a file, a cache, a global, a field), list the code that writes it and the code that reads it.
- **Flows.** Draw each main flow as the run showed it, with its source map as [evidence](../EVIDENCE.md#diagrams) says.

Checkpoint: lead with the differences, because a reviewer handed a whole map approves it unread. Show each *not stated* and *not found* relationship, each hidden part, and each state with more than one writer, with its pinned line or run. For each difference, ask whether it is intended, in which case the stated design is what changes, or drift.

Done when every stated relationship has a result with the edges behind it, every piece of state has its writers, and each difference carries the user's answer or a marked default.

## 5. Name what is wrong

Give each problem one of five names, with the evidence that confirms it:

- **Scattered rule:** one rule decided at more than one decision site. Nothing in the code says the sites must change together.
- **Misplaced logic:** a decision made away from the owner of the state or rule it decides, such as a business rule in a serializer.
- **Needless link:** pieces tied together that change for different reasons, such as stable code importing code that changes weekly, or a general function with a parameter one caller understands.
- **Surplus:** code with no reason of its own to exist: a wrapper that only delegates, an extension point nothing varies, a setting nothing changes, code nothing reaches. Test it by deletion: if deleting it makes complexity vanish, it was surplus; if the complexity reappears in every caller, it was earning its place.
- **Unjustified special case:** a special case with no caller, input, test, incident, or decision behind it.

Classify every special case as [special cases](references/special-cases.md) says, by whether anything reaches it and by what it points to. A special case is first a lead to something larger: a requirement the design never accounted for, a producer that emits a state it should not, or a boundary nobody made explicit. Name that, and the local line second.

Rank the findings by what they cost today: how often the files change, times how many places one change must touch. A problem in code nobody changes is listed with *no action*.

Record what looked wrong and is fine, with the reason the user or the history gave, so that the next run does not raise it again.

Done when every capability with more than one decision site for a rule, every difference the user called drift, and every special case in scope has a finding or a stated reason it is fine.

## 6. Propose the rework

When the deliverable includes a proposal, follow [rework](references/rework.md): group the findings under the change that removes them, worked out as if the system had known today's requirements from the start; offer two or three materially different **targets**, one of which leaves the code as it is; and give for the recommended target the ordered steps, each behavior-preserving, each with the **pin** that protects it. A pin is a test that fails when the behavior changes, seen failing once against a deliberate break.

Checkpoint: the user chooses the target. Changing a behavior is never part of a rework step: a defect or an unwanted fallback found on the way is its own decision, handed to [fix-bug](../fix-bug/SKILL.md) or [plan-change](../plan-change/SKILL.md).

Done when the user has chosen a target, or the choice is listed as open with the recommendation; and every step of that target names its files, its pin, and the check that proves behavior unchanged.

## 7. Record and deliver

Keep one `rework-map.md` at the investigation location. For a new map, fill [map-template.md](references/map-template.md) as [map-format.md](references/map-format.md) says, removing unused prompts; update an existing map in place. Before every delivery, including each checkpoint, run `python3 <package>/skills/render_page.py <rework-map.md> --check --sync-labels --markdown-only`, and for a chosen HTML companion follow the [shared page workflow](../HTML-PAGES.md) and run the check without `--markdown-only`.

Before delivering, check that:

- Every relationship in the map has its command, pinned line, or the label *inferred*, and every flow has its run or its named obstruction.
- Every answer the user gave is in the map beside the claim it settles, and every default applied without an answer is marked as a default with its alternative.
- No proposed removal rests on missing test coverage alone.
- The map has been compared with its sources as [evidence](../EVIDENCE.md#check-before-delivery) says. Use a [second reader](../FRESH-REVIEW.md) when the rework is large or the user asks.

Deliver in chat: what the component does, the differences from the stated design that matter most, the recommended target, the questions still open, and the link to the map. Then hand over the next command. For the rework: `/aantoniadis-skills:plan-change Plan the rework of <component>. Reuse the rework map at <path>; the chosen target is <name>.` (`$` instead of `/` in Codex). For one contained step in familiar code, the step text is the scope for a direct implementation. When the user confirmed a difference as intended or chose a target, offer the matching update to the project's design documentation or decision records, and write it only within authorization, as [asking](../ASKING.md) says.

Done when the map passes the check, the chat states the applied choices, and the user has the next command or the questions that block it.

## Working with the user

Each checkpoint is a round from [asking](../ASKING.md): number the questions, put the recommended answer first, and word each so that "yes" accepts it. Group questions that have one answer, such as six guards on the same value, into one. Ask the questions with the most consequence first, and keep the rest in the map's question table.

When no one answers, as in an unattended run, every question about intent takes its conservative default: the behavior is intended, the special case stays, and the stated design stands. Mark each as a default, and say in the proposal what changes under the other answer.

A follow-up, such as "the guard in the importer came from an outage", resumes the same map: recheck the revision, record the answer beside its claim, and update the findings, targets, and steps it changes.

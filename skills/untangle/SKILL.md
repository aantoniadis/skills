---
name: untangle
description: Maps how an existing component really works, finds one rule's logic scattered across modules and layers, capabilities nobody documented, behavior no test protects, and guards or fallbacks nobody can justify, and proposes a rework that gives each rule one owner. Use when existing code has become hard to follow or change, when the user asks to de-slop, clean up, untangle, or restructure a component, to map the architecture as it is today, or to compare the code with its documented design. Not for explaining one flow (explain), planning a behavior change (plan-change), or finding defects in a diff (find-bugs).
argument-hint: "<component, directory, or flow to untangle; what hurts about it, if you know>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Untangle

Produce the **rework map** of one component: what it does, how it is built today, where that differs from what people believe, and a rework the user can choose. In the target, every rule and every piece of state has one **owner**: the module that decides the rule or writes the state. Application code stays as it is. The only change to the project is the **lock tests** of step 7, which come with every rework proposal: tests that record what the code does today, so the rework that follows cannot change it unnoticed. Probes and scratch copies live in the investigation location.

Three rules hold for the whole task:

- **Relationships come from tools and runs.** Record a call, a dependency, or "this input reaches that line" from a resolver, a search result, or an execution, and keep the command. Names, groupings, and explanations are yours to write. A relationship taken from a comment, a name, or your reading alone carries the label *inferred*.
- **The user supplies intent; you supply facts.** Answer every question the code, its history, or a run can answer. Ask the user what only a person knows: why something exists, whether a behavior is intended, which flows matter, and which design they want. Write each answer into the map, so a later session reads it instead of asking again.
- **What nobody can explain stays.** A guard, fallback, or branch whose reason is unknown is kept and listed as a question. A removal is proposed only on the evidence [special cases](references/special-cases.md) requires.

Steps 2 to 4 describe the component. Judgment starts at step 5, so the user corrects a description before reading an argument built on it. The honest result may be small: when the structure is sound, say so, and deliver the map, the behavior no test protects, and the questions.

## 1. Agree the scope and establish what runs

Before the kickoff, look at the target's size and its history, because the scope recommendation reads both: `git rev-parse --is-shallow-repository`. Deepen a shallow clone within existing authorization, or state the number of commits every history count rests on.

Hold the kickoff round from [asking](../ASKING.md), with the questions the request leaves open: the scope, one component or flow with a proposed starting path (when the user names none, recommend the place where change is paid most, from the most changed files that [`change_coupling.py`](scripts/change_coupling.py) prints); the deliverable, the map alone or the map with a rework proposal (recommend the proposal); a proposal includes its lock tests written into the project, because a rework without them changes behavior unnoticed, and leaves them out only when the user says the project must not change; an HTML companion or text only (recommend HTML when the scope has more than one flow); and how to work together, a checkpoint after steps 2, 4, and 6 (recommend it) or a guided walk through the code, where you step through one flow with excerpts and run results and the user directs the depth, following the trace loop of [explain](../explain/SKILL.md) as a helper run.

Then establish the ground, using [CODE-TOOLS.md](../CODE-TOOLS.md) to select capabilities and reuse local preparation. Create the investigation location and its run records first, under the topic `untangle-<component>`, where a follow-up looks for the map:

```bash
inv="$(python3 <package>/skills/investigation_dir.py untangle-<component> <project>)" && mkdir -p "$inv/runs" && echo "$inv"
```

- Record the repository root, revision, and local changes from the source directory, and the configuration the runs use: the settings, flags, and environment a baseline or probe needs.
- Run the scope's test suite once as it is. Keep the command, result, and duration in `$inv/runs/`. This run is the baseline every later probe is compared with.
- Run it once more with coverage recorded per test, where the coverage tool supports it, and keep the command and the data in `$inv/runs/`. [Census](references/census.md) says how the data is read.

When the scope cannot run here, try the repair route of [setup-tools](../setup-tools/SKILL.md). If it still cannot run, say so at the top of the map: every claim is then read at the line, no special case gets a reach probe, and the map proposes no removal.

Done when the scope is a named set of paths, the revision is recorded, and the baseline has a recorded result or a named obstruction.

## 2. Record the stated design

Work from the outside in, before reading internals: the structure you find is evidence, and the stated design is what it is measured against.

- **Capabilities.** List what the component does for its consumers, in the project's own domain words, from its entry points (routes, commands, exported functions, jobs, event handlers), its callers, its documentation, and its test names. Aim for 5 to 15. Give a capability of its own to what every entry point passes through, such as authentication, authorization, error translation, or a mode switch, even though no entry point is named after it: scattered rules collect there. A test name states intent; the code under it establishes behavior.
- **Stated dependencies.** Collect the components the documentation, decision records, instruction files, and directory layout name, and the dependencies allowed between them.
- **Stated rules.** Quote, with its link, each sentence that says what a part must or must not do, such as "the API layer decides nothing about money" or "every backend path is built in the client module". A design is often stated more in rules than in dependencies.

When nothing states a design, write the one the entry points and layout imply, label it *inferred*, and make it the first thing the user corrects.

Checkpoint: show the capability list, the stated dependencies, and the stated rules. Ask what is missing or wrong, which flows matter most, where the code hurts, and which oddities are deliberate, such as a guard added after an incident.

Done when every entry point in scope belongs to a capability or is listed as unassigned, and every stated dependency and rule has its source: a quote, the user's answer, or *inferred*.

## 3. Take a census of each capability

A **decision site** is a place that decides something about a capability: a condition, a default, a validation, a transformation, or a write to its state. The **census** of a capability is every decision site, wherever it lives: helpers, validators, serializers, middleware, configuration, queries, templates. Take it as [census](references/census.md) says, from five kinds of evidence (text, references, execution, history, and a deliberate break), and read where they disagree:

- Code a scenario executes that no search for the capability's words found is a hidden part of it.
- Code those words find that no scenario executes is a lead to dead code.
- Files that change together with no dependency between them are a lead to one rule kept in two places.
- A decision you break on purpose while every test stays green is behavior no test protects. Break the decisions that matter most: a check on who may do what, a rule about money or data, a value another system reads.

In the same pass, list two more things, each with its script and your own reading:

- The scope's special cases, with [`special_cases.py`](scripts/special_cases.py). A **special case** is code that exists for one situation: a guard, a default, an error turned into a value, a retry, a compatibility path, a parameter one caller sets.
- The scope's shared data, with [`shared_data.py`](scripts/shared_data.py): state that more than one piece of code changes, and **shapeless data**, a hash, dict, or untyped object passed between modules whose keys are decided at the sites that use them. For each piece of shapeless data, record where it is built, and for each key the sites that write it and read it. Then freeze it where it is handed over, in a scratch worktree, and run the tests: each failure names a site that changes it afterwards. For state held in a database or a file, start from every caller of the methods that write it, and run two writers interleaved. [Census](references/census.md#state-and-data-that-travels) has the steps.

A **lead** is where to look. It enters the map only after you have read the code on both sides and, where a run decides it, run it.

Take the capabilities in the user's order of importance, or, when nobody has said, by how often their files change. Inspect each as far as the session allows and say how far: *inspected*, *partly inspected* with what was read, or *not inspected* with the reason. Where text is itself the interface, such as a prompt, a tool description, or generated help, say whether it was compared with the code. When one session cannot inspect every capability, give each remaining one to an [investigator](../INVESTIGATE.md) through [native delegation](../WORKERS.md), with the stated design, the baseline, and the census reference; the map is the shared record. Split the work by capability, because a split by layer hides exactly the scattering this step looks for.

Done when every capability has its decision sites listed with pinned lines and the kinds of evidence taken for it, or says how far it was inspected and why; every lead the map relies on is confirmed by reading or a run; and the leads not followed are counted in the map's limits.

## 4. Draw the map as it is, and compare

Draw four views, each from extracted facts:

- **Dependencies.** Get the edges between the scope's files from the ecosystem's resolver, or from [`import_edges.py`](scripts/import_edges.py) as a floor. Write the stated dependencies as the JSON that [`design_conformance.py`](scripts/design_conformance.py) reads, and run it: every relationship comes out *as stated*, *not stated* (the code has it and the design does not allow it), or *not found* (the design names it and no edge shows it). Read the file edges behind each result that is not *as stated*.
- **Stated rules.** Check each quoted rule against the census: *holds*, with the search or run that covers it; *broken*, with the pinned line or run that breaks it; or *not checked*.
- **State and data.** For each piece of state the scope keeps (a table, a file, a cache, a global, a class-level variable, a field), list the code that writes it and the code that reads it. For each piece of shapeless data, list its keys with their writers and readers, and the sites that change it after it is handed over. A component that keeps no state of its own and passes only declared values says so in one sentence, with the search that shows it.
- **Flows.** Draw each main flow from the source, labeled *source*, and mark the steps a recorded run executed, with its source map as [evidence](../EVIDENCE.md#diagrams) says. Where an ordered trace is cheap, such as one end-to-end test under a tracer, record it.

Checkpoint: lead with the differences, because a reviewer handed a whole map approves it unread. Show each *not stated* and *not found* dependency, each broken rule, each hidden part, each state with more than one writer, each piece of data changed after it is handed over, and each behavior no test protects, with its pinned line or run. For each difference, ask whether it is intended, in which case the stated design is what changes, or drift.

Done when every stated dependency and rule has a result with its evidence, every piece of state has its writers, and each difference carries the user's answer or is marked *open*.

## 5. Name what is wrong

Sort what you found into three places.

**Behavior to decide** is what the component does that may be wrong or unwanted: a possible defect, two sites that give different results for the same input, a fallback that changes what a consumer sees. It is not a structure problem and gets no structure name. List each one near the top of the map with its run, and its handoff to [fix-bug](../fix-bug/SKILL.md) or [plan-change](../plan-change/SKILL.md). A user who no longer trusts the code reads these first.

**Structure findings** each get one of seven names, with the evidence that confirms it:

- **Scattered rule:** one rule decided at more than one decision site. Nothing in the code says the sites must change together.
- **Misplaced logic:** a decision made away from the owner of the state or rule it decides, such as a business rule in a serializer.
- **Needless link:** pieces tied together that change for different reasons, such as stable code importing code that changes weekly, or a general function with a parameter one caller understands.
- **Surplus:** code with no reason of its own to exist: a wrapper that only delegates, an extension point nothing varies, a setting nothing changes, code nothing reaches. Test it by deletion: if deleting it makes complexity vanish, it was surplus; if the complexity reappears in every caller, it was earning its place.
- **Shared mutable state:** state that more than one module writes, or data that a module changes after another module handed it over. A reader cannot tell what a value holds without knowing every writer and the order they ran in.
- **Shapeless data:** data passed between modules with no declared shape, so each site that reads or writes a key decides part of it. Its signs are a key written in several files, a key read with a default, and two readers whose defaults differ. Many unjustified special cases are its symptom: a reader defends itself because nothing says what the data holds.
- **Unjustified special case:** a special case with no caller, input, test, incident, or decision behind it.

Classify every special case that has a row in the map as [special cases](references/special-cases.md) says, by whether anything reaches it and by what it points to. A special case is first a lead to something larger: a requirement the design never accounted for, a producer that emits a state it should not, or a boundary nobody made explicit. Name that, and the local line second. A special case that is *reached* and whose handling bends the design, as [corner cases](../CORNER-CASES.md) lists, gets a corner-case card in the map's *Corner cases* table: its reach and harm, what each change to the general path pays for it, and the options, such as isolating it at the edge or rejecting the case at the boundary. Until the user chooses, it stays as it is.

Rank the structure findings by what they cost today: how many places one change to the rule must touch, and how often the rule itself has changed. Take that from the history of the rule's lines or its discriminator; a file's change count says how busy the file is, not the rule. A problem in code nobody changes is listed with *no action*.

**Looks wrong, is fine** records what a reader would flag and the reason the user or the history gave, so that the next run does not raise it again.

Done when every capability with more than one decision site for a rule, every difference the user called drift, and every special case with a row has a finding, a place under behavior to decide, or a stated reason it is fine.

## 6. Propose the rework

When the deliverable includes a proposal, follow [rework](references/rework.md): group the findings under the change that removes them, worked out as if the system had known today's requirements from the start; describe the recommended **target** in full and each alternative in a few sentences, one of which leaves the structure as it is; and give for the recommended target the ordered steps, each behavior-preserving, each with the **pin** that protects it. A pin is a test that fails when the behavior changes, seen failing once against a deliberate break. The breaks of step 3 already show which behaviors have one.

When the findings do not justify a restructuring, recommend leaving the structure as it is. The proposal is then the pins for the behavior no test protects, and the check that keeps the stated design true; step 7 still writes those pins.

Checkpoint: the user chooses the target. Changing a behavior is never part of a rework step: it stays under behavior to decide.

Done when the user has chosen a target, or the choice is listed as open with the recommendation; and every step of that target names its files, its pin, and the check that proves behavior unchanged.

## 7. Lock the behavior

With a rework proposal, write the lock tests into the project's tests now, before anyone moves code. A request for a rework, or no answer, does not stop them: they change no behavior, and the rework is unsafe without them. Only when the user said the project must not change, write them at the investigation location and say in the delivery that they are not in the project. Follow [lock tests](references/lock-tests.md):

1. **List what to lock.** Every behavior a step of the chosen target moves, and every behavior the deliberate breaks showed no test protects. Behavior already pinned by a test that the breaks turned red needs nothing new.
2. **Write each test at a seam the rework keeps,** in the project's own test framework, layout, and naming, so the test still runs once the code behind the seam has moved. A probe from the census is its starting point. Assert what the code returns today, including behavior listed under behavior to decide: name such a test after what it records, such as "records that a gold quote is 38.00", and mark it as recording a value under decision, so the decision changes the test on purpose.
3. **See each one fail.** In a scratch worktree, make the break the test is meant to catch and run the test; record the break and the red result. Restore, run the whole suite, and record it green. A test that stays green under its break locks nothing: rewrite it at another seam, or record the gap.

Leave the tests in the working tree, and commit them only within authorization, as [asking](../ASKING.md) says. They are the first step of the rework: the steps that follow name them as their pins.

Done when every behavior on the list has a test seen red under its break and green on the code as it is, or a recorded reason it has none, and the whole suite passes.

## 8. Record and deliver

Keep one `rework-map.md` at the investigation location. For a new map, fill [map-template.md](references/map-template.md) as [map-format.md](references/map-format.md) says, removing unused prompts; update an existing map in place. Write the **structure view** into it as a `structure-view` fence, as [map-format](references/map-format.md#structure-view) says: the page draws it as a picture you can switch between today and the proposal, and the tables carry the same content as text. Before every delivery, including each checkpoint, run `python3 <package>/skills/render_page.py <rework-map.md> --check --sync-labels --markdown-only`, and for a chosen HTML companion follow the [shared page workflow](../HTML-PAGES.md) and run the check without `--markdown-only`.

The check confirms that a pinned line exists. It cannot tell whether the line says what your sentence claims. Print every pin beside its source text, read the list against the map, and recount every number the map states:

```bash
python3 <package>/skills/untangle/scripts/pinned_lines.py <rework-map.md> --repo <project>
```

Before delivering, check also that:

- Every relationship in the map has its command, pinned line, or the label *inferred*, and every flow says which of its steps a run executed.
- Every answer the user gave is in the map beside the claim it settles, and every question nobody answered is marked *open* with its default.
- No proposed removal rests on missing test coverage alone.
- Every lock test is listed in the map with the behavior it locks, the break it failed under, and the suite run that passed; and no application code changed.
- A [second reader](../FRESH-REVIEW.md) has compared the map with its sources when the recommended target touches more than five files, removes a check at a trust boundary, or the user asks.

Deliver in chat: what the component does, the behavior to decide, the differences from the stated design that matter most, the recommended target, the lock tests written, the questions still open, and the link to the map. Then hand over the next command. For the rework: `/aantoniadis-skills:plan-change Plan the rework of <component>. Reuse the rework map at <path>; the chosen target is <name>.` (`$` instead of `/` in Codex). For one contained step in familiar code, the step text is the scope for a direct implementation. When the user confirmed a difference as intended or chose a target, offer the matching update to the project's design documentation or decision records, and write it only within authorization, as [asking](../ASKING.md) says.

Done when the map passes the check, the pins have been read against it, the chat states the applied choices, and the user has the next command or the questions that block it.

## Working with the user

Each checkpoint is a round from [asking](../ASKING.md): number the questions, put the recommended answer first, and word each so that "yes" accepts it. Group questions that have one answer, such as six guards on the same value, into one. Ask the questions with the most consequence first, and keep the rest in the map's question table.

When nobody answers, as in an unattended run, hold no checkpoint: continue through the steps, write each checkpoint's questions into the question table, and deliver once at the end. Then:

- A difference between the code and the stated design is *open*: neither drift nor intended.
- A special case stays.
- The lock tests of a rework proposal are written into the project's tests.
- Rework steps include only moves that keep behavior and hold under either answer. A move that depends on an open answer is listed as waiting for it.

After the rework lands, a follow-up re-measures it against the same map. At the new revision, run the lock tests and the conformance check again, and take the census again for the rules and data the target names. Fill the map's *After the rework* section: for each line of the target's **Measure**, the value before, the value now, and *met* or *not met* with the run. A rule still decided in more than one file, or a dependency still *not stated*, is a finding of the rework, and its step is reopened. A lock test that changed without a decision behind it is behavior to decide.

A follow-up, such as "the guard in the importer came from an outage", resumes the same map: recheck the revision, record the answer beside its claim, and update the findings, targets, and steps it changes.

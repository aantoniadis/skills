---
name: fix-bug
description: Finds the cause of a reported bug and fixes or diagnoses it, with a demonstrated reproduction, a regression test that went red then green, and a diagnosis note with an HTML page a reviewer can verify. Use when a test or CI job fails, an issue reports wrong behavior, a production symptom arrives with logs or a trace, or the user asks to fix, debug, or diagnose a bug; it settles first whether the behavior is a bug. Not for defects in a diff with no reported symptom (find-bugs), how working code behaves (explain), deciding new behavior (plan-change), or migrating a tool's configuration to a new version. Matt Pocock's diagnosing-bugs and superpowers' systematic-debugging also fire on bug reports; when either is installed, invoke this skill by name.
argument-hint: "<the symptom: a failing test, a CI link, an issue, or a log excerpt; what should happen, if known>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Fix bug

Deliver a demonstrated cause and, when fixing is in scope, a fix proven by a regression test that went *red* before it and green after it. A *red* is the loop failing on the user's exact symptom. It comes before every cause claim and every fix, except in the [artifacts-only branch](#artifacts-only-branch); reading code may start at once. Keep a record a reviewer can check line by line.

## 1. Kickoff and contract

Hold the kickoff round from [asking](../ASKING.md) first, with the questions the request leaves open: fix plus record, or diagnosis only (recommend the fix); an HTML page or text (recommend HTML); the fix left in the working tree, or committed (recommend the working tree). Apply a choice the request states without asking. Diagnosis only follows the [diagnosis-only branch](#diagnosis-only-branch). The routine investigation location holds `diagnosis.md`, its page, and `runs/bugs/<n>/`, one directory per bug numbered from 1. The first delivery states the applied choices in its `Kickoff:` line.

Pin the **contract**, what should happen, with its evidence, from the strongest source available: the failing assertion and the behavior it was written to pin, a plan decision or spec, the issue text, documentation, or the intent of the commit or PR that wrote the code. Quote and link the source that decides. The verdict is one of three:

- **A bug:** continue to step 2. A fix starts only on this verdict.
- **Works as specified:** write the note with the mismatch and the deciding source, and deliver it through step 6 with no fix.
- **An open behavior decision:** write the note with the question and its owner, ask the owner, and offer the [plan-change](../plan-change/SKILL.md) handoff.

Before the first edit to a project file, save `git status --porcelain` under `runs/bugs/<n>/`, and capture each already-modified file you will edit as [evidence](../EVIDENCE.md#capture-a-local-snapshot) says, so the user's own edits stay apart from the fix.

Done when the `Kickoff:` line is ready, the contract is pinned with one quoted or linked source, and the starting working-tree state is saved or no edit is planned.

## 2. Reproduce

Build the **loop**: one saved command that goes red on the exact symptom and green once fixed. Keep it *tight*: deterministic, seconds long, and runnable unattended. Raise a flaky symptom's reproduction rate, by looping, parallel runs, stress, or narrowed timing, until the red is reliable, and record the rate.

- **A failing test or CI job** is the loop once it fails here for the reason it failed there. Compare the message and the environment before trusting it; a failure that only the CI environment produces is an environment gap to record, not the bug.
- **Issue steps** become a focused test, a script, a request, or a CLI call through the public boundary. When the project's test or run command is not evident from its files, the [local tool record](../TOOL-SETUP.md) or [CODE-TOOLS.md](../CODE-TOOLS.md) names it.
- **Logs or a trace with no steps**: pin each stack and log line to source, infer the inputs, and attempt a loop from them. When none can be built, take the [artifacts-only branch](#artifacts-only-branch).

A loop that runs against a stand-in for the component that carries the bug, such as a fake database or a mocked service, reproduces a *model*: the Checked line says so after *reproduced* and *test red then green*, and the next step names the run on the real component.

Minimise: cut inputs, callers, configuration, and steps one at a time, rerunning after each cut, until every remaining element is load-bearing. Save the script before running it so the saved file is the one that ran, check that it loads the checkout and dependencies you mean, and keep the command, output, revision, and environment under `runs/bugs/<n>/`. Ordinary local checks proceed; ask before a probe with material cost or side effects, such as starting a service, pulling an image, or touching shared data, and continue independent work while waiting. Redact secrets in every shown command, output, and captured artifact; quote only the lines that carry the signal.

Done when one saved command has run and gone red on the exact symptom, with its output recorded, or the artifacts-only branch is declared with what was tried.

## 3. Find the cause

Rank three to five falsifiable hypotheses before testing any, each with its prediction: if this is the cause, then this change makes the loop go green, or that change makes it worse. Name each hypothesis by what it says. When the red output pins the cause line and that line has one caller, one hypothesis with its probe is enough. Show the ranking when the user is present, since they often re-rank it from what they know, and continue without waiting for an answer.

Probe the cheapest first, one variable per probe: a debugger or REPL before logs, logs at the boundaries that separate hypotheses, each tagged with one prefix such as `[DEBUG-a4f2]` so one grep removes them. When more than one hypothesis survives and the probes are independent, use [investigator](../INVESTIGATE.md) workers through [native delegation](../WORKERS.md), one hypothesis each, with the loop command, the saved evidence, and the user's authorization. For a performance symptom, measure first: a baseline timing, a profile, or a query plan, then bisect the cost.

Record each hypothesis as supported, contradicted with its counterevidence, or unresolved with the missing check. A guard, a cleanup, a configuration restriction, or a pinning test is counterevidence; an assumption about timing or deployment is not. Pin the **cause**: the line, the trigger, and the contract it violates.

Done when one hypothesis is supported by a probe at the pinned line and every other is recorded as contradicted or unresolved.

## 4. Trace origin and reach

Run each when its trigger holds, before any fix lands: together they decide between a revert and a forward fix, and which callers the fix must cover. Record each in the note as done, or as skipped with its reason.

- **Origin**, when "it used to work", a passing earlier run, a release note, or history suggests a regression: bisect with the loop in a disposable clone or worktree. Wrap the loop so that a build, install, or unrelated failure exits 125, which `git bisect run` skips, and only the symptom exits 1; pass the saved script by absolute path, as in `git bisect run /abs/path/loop.sh`. Afterwards run `git bisect reset` and remove the clone or worktree, as with `git worktree remove <path>`. Quote the breaking commit's intent from its message, PR, or issue, and choose a revert or a forward fix. The fix preserves the quoted intent.
- **Reach**, when the cause sits in code with two or more callers or in a copied pattern: list every caller and path that hits the line or the assumption, by symbol search and by searching for the copied pattern. Each caller is affected, so the fix and the test cover it, or cleared with pinned counterevidence.

Done when origin and reach each carry a result with evidence or a skip reason.

## 5. Fix and prove it

Write the regression test first, at a seam that exercises the real bug pattern as it occurs at the call site, and watch it fail. A seam too shallow for the pattern gives false confidence; when no correct seam exists, record the gap and keep the loop as the proof. Fix at the cause with the smallest change that satisfies the contract for every affected caller; a patch at the symptom site leaves the cause in place. Watch the regression test pass, then rerun the original, unminimised loop. Remove tagged instrumentation and scratch files outside `runs/bugs/<n>/`.

**Consequence**, when the fix changes a shared producer or a contract: follow [behavior comparison](../BEHAVIOR-COMPARISON.md) for its other consumers through their next action, and run a focused check where a consequential uncertainty remains. Otherwise record consequence as skipped with the reason.

Done when the original loop is green, the regression test has a recorded red and green or the missing seam is recorded, consequence carries a result or a skip reason, and a grep for the instrumentation prefix returns nothing.

## 6. Record and deliver

Fill [diagnosis-template.md](references/diagnosis-template.md) at the investigation location, removing unused prompts, and compose it as [diagnosis-page.md](references/diagnosis-page.md) says. Pin committed code at its commit; capture uncommitted bytes beside the note as [evidence](../EVIDENCE.md#capture-a-local-snapshot) says, and cite an applied fix as the diff of the files it touched, taken against the step 1 capture for a file that was already modified. Before every delivery, follow the [shared page workflow](../HTML-PAGES.md#fill-the-content-then-render): finish the note and the evidence it links, render the page when HTML was chosen, then run `python3 <package>/skills/render_page.py <diagnosis.md> --check --sync-labels`, with `--markdown-only` for text. Repair every reported problem before presenting the note as complete. Use a [second reader](../FRESH-REVIEW.md) for a consequential fix when useful.

Deliver the verdict and the fix state in chat, link the note and any page, and hand over the next command: HumanLayer's `visual-pr` when an applied fix is ready for a PR, user-invoked, so give the command with the note and run record as context; `/aantoniadis-skills:plan-change` (`$` instead of `/` in Codex) when a behavior decision stayed open. Commit only when the kickoff or the prompt authorized it. Publication and application changes beyond the fix need their own authorization, as [asking](../ASKING.md) says.

Done when the note and any page pass the checker, the chat states the verdict, the fix state, and the applied choices, and the user has the next command or the evidence and authorization still needed.

## Diagnosis-only branch

Keep application code and project tests unchanged; save probes at the investigation location. Run steps 1 to 4, then deliver through step 6. The note lists affected callers as unfixed, records consequence as skipped because no fix was applied, and marks the regression test *test not verified*. A fix direction is optional and stays *proposed*; proposing one does not authorize application changes. The chat names what the user would authorize to continue to a fix.

## Artifacts-only branch

With logs or a trace and no loop after a real attempt, deliver the diagnosis as ranked hypotheses with *inferred* labels: each names the artifact lines and source lines it rests on, the probe that would settle it, and the access or artifact that would give a loop. A fix stays *proposed*: a diff when the inspected API contract supports one, otherwise the direction and the missing contract. A fix lands without a red only on the user's explicit answer to a checkpoint whose recommended option keeps the fix proposed; a defaulted or missing answer, as in a non-interactive session, keeps it proposed. When it lands, the note's Checked line carries *not reproduced* and *fixed*, the regression test is written where a correct seam exists or the missing seam is recorded, and the test stays *test not verified* until its red and green runs are recorded.

## Working beside other debugging skills

When the host has already started another debugging discipline in this session, continue under these steps: the loop criteria are the same, the contract comes first, and the note is the deliverable.

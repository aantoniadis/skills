# find-bugs

Return actionable defects in a change, ranked by impact, likelihood, recovery,
and confidence. Findings distinguish observed results from source-supported
predictions and include material questions and review limits. A ledger of
coverage units makes the search repeatable: two runs on the same pins start from
the same list, and every unit ends with a disposition.

## How it works

1. **Pin scope.** Record the base/head comparison and supported conditions.
   For a working-tree review, identify staged, unstaged, and untracked scope and
   retain the relevant dirty source. Read changed source; name excluded or
   unavailable material.
2. **Sweep the change.** A script seeds one coverage unit per changed symbol, or
   per hunk when no symbol encloses it, with the consumers outside the change
   that reference it. Apply every defect class to each unit — boundary, errors,
   state, consumers, concurrency, normalization, cost, compatibility — and record
   the source fact that settles each class. Run the change-level checks once:
   untested lines, weakened checks, dependency compatibility, static diagnostics,
   history, and supplied hypotheses. Each hypothesis needs a plausible trigger,
   predicted result, and contract it would violate. A confirmed defect sends the
   search for its variants across the rest of the change. Close every unit with a
   disposition; a unit the pass cannot reach is deferred with its reason.
3. **Resolve uncertainty.** Reuse applicable source and run evidence. A source-only
   search can return inferred findings with a proposed settling check. When a
   probe is useful and authorized, run the smallest adequate check against the intended checkout and
   dependencies. Compare base and head under equivalent conditions, with the base
   in a disposable worktree so your checkout stays untouched. Retain
   scripts, commands, output, inputs, and environment limits. A probe confirms
   an observation; the contract determines whether it is a defect.
4. **Check and deliver.** A fresh reader looks for coverage gaps only: a unit
   closed without a source fact, changed source with no unit, a consumer listed
   but unread. Work every accepted gap, then run a second pass; only a pass that
   accepts nothing ends the check, and a third pass's gaps are deferred with
   their reason. Seek counterevidence, distinguish new and worsened
   defects from unchanged pre-existing behavior, and retain actionable static
   findings. Instrumentation is useful when it observes a real failure. Ask the
   author only about material missing intent or facts. Return ranked findings
   under `## Defects`, with evidence and relevant questions, and state in plain
   words what was checked and what was left unchecked. A material
   pre-existing defect that a probe executed goes under `## Outside the change`.
   A confirmed consequence dropped as immaterial goes under
   `## Minor observations`, one line naming the condition that would make it
   material. The ledger, detailed drops, and tool logs stay in the investigation
   notes.

Dependency checks use the project's supported-version commands, constraints,
and resolver in a fresh environment.

The ledger helper reads two commits, or the working tree against HEAD when no
base is given, and writes JSON to stdout: the units, their changed lines, a hash
of the source each unit covers, and the consumers outside the change. `--coarse`
merges units per file for a bounded pass on a large diff. `--prior` carries an
earlier ledger's dispositions as leads and its gaps as work, never as closure.
`--check` reads the saved ledger and reports the units, classes, and change
checks with no disposition, exiting 1 while coverage is incomplete. Definition
patterns cover common Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, and
PHP idioms; another language gets hunk units.

The optional test-coverage helper reads two committed revisions and an existing
coverage report. It reports executed, missing, excluded, and unclassified added
lines. Coverage paths must match the repository root, without suffix guessing;
missing reports or Git failures produce an error. Istanbul/Vitest results cover
statement starts, not every line of multiline statements. The caller checks
that the report belongs to the inspected source and environment.

Prompt shape:

```text
/aantoniadis-skills:find-bugs <PR URL, branch, or "the working tree"> <anything the finder should know>
```

`pr-review-guide` and `check-acceptance` call it as a helper for their search for
bugs; the returned list becomes bug cards, linked from the guide's *you decide*
and *check it* items or from the acceptance report's requirement rows.
Unobserved base/head results remain labeled predictions. A passing diagnostic
can establish the predicted observation while exposing a defect; the check's
result and the finding's status are separate. The calling skill owns integration.


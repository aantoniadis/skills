# find-bugs

Return actionable defects in a change, ranked by impact, likelihood, recovery,
and confidence. Findings distinguish observed results from source-supported
predictions and include material questions and review limits.

## How it works

1. **Pin scope.** Record the base/head comparison and supported conditions.
   For a working-tree review, identify staged, unstaged, and untracked scope and
   retain the relevant dirty source. Read changed source and consequential
   callers; name excluded or unavailable material.
2. **Investigate leads.** Select useful project tools and applicable prepared
   results. Coverage gaps, dependency compatibility, new consumers, static
   diagnostics, and history can expose hypotheses. Each hypothesis needs a
   plausible trigger, predicted result, and contract it would violate.
3. **Resolve uncertainty.** Reuse applicable source and run evidence. A source-only
   search can return inferred findings with a proposed settling check. When a
   probe is useful and authorized, run the smallest adequate check against the intended checkout and
   dependencies. Compare base and head under equivalent conditions. Retain
   scripts, commands, output, inputs, and environment limits. A probe confirms
   an observation; the contract determines whether it is a defect.
4. **Check and deliver.** Seek counterevidence, distinguish new and worsened
   defects from unchanged pre-existing behavior, and retain actionable static
   findings. Instrumentation is useful when it observes a real failure. Ask the
   author only about material missing intent or facts. Return ranked findings
   under `## Defects`, with evidence and relevant questions; detailed drops and
   tool logs stay in the investigation notes.

Dependency checks use the project's supported-version commands, constraints,
and resolver in a fresh environment.

The optional coverage helper reads two committed revisions and an existing
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


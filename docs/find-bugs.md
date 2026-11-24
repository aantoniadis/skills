# find-bugs

Return actionable defects in a change, ranked by impact, likelihood, recovery,
and confidence. Findings distinguish observed results from source-supported
predictions and include material questions and review limits.

One read of a change finds part of what repeated reads find. On two public
pull requests, one read reported about a third to a half of what five reads
reported together. The default is one read. A **thorough** search, asked for
in words such as "thorough" or "find everything", runs four or five
independent finders. One is general. Three have their own focus: what code
outside the change sees (callers, subclasses, hooks, docs), the values the
change treats differently (arguments, defaults, options, platforms), and
shared state. A fifth makes each added file, process, or network call fail
and gives each new path a hostile filesystem state; it runs when the change
adds five or more such calls, and otherwise the lead fails each one itself.
The lead runs the type checker and the other shared checks once, records a
decision for every candidate the finders return, and confirms each delivered
one with a probe at base and head. A drop names its ground: absent at the
head, the same at the base, or documented intent. A confirmed small change
is delivered as a minor observation. `evals/thorough-focus/` records how
focused finders compared with three general finders on four public pull
requests. Neither depth is a completeness claim: the
delivery says how many reads searched the change.

## How it works

1. **Pin scope.** Record the base/head comparison and supported conditions.
   For a working-tree review, identify staged, unstaged, and untracked scope and
   retain the relevant dirty source. Read changed source and consequential
   callers; name excluded or unavailable material.
2. **Investigate leads.** In a thorough search, each finder gets the pins and
   nothing from the lead's own reading, runs code where the source leaves the
   outcome open, and returns every candidate it could not contradict. Every
   search compares the project's type checker or linter
   at base and head over the repository root. Select useful project tools and applicable prepared
   results. Coverage gaps, dependency compatibility, new consumers,
   and history can expose hypotheses. Each hypothesis needs a
   plausible trigger, predicted result, and contract it would violate.
3. **Resolve uncertainty.** Reuse applicable source and run evidence. A source-only
   search can return inferred findings with a proposed settling check. When a
   probe is useful and authorized, run the smallest adequate check against the intended checkout and
   dependencies. In a thorough search the lead confirms each delivered candidate once.
   Compare base and head under equivalent conditions, with the base
   in a disposable worktree so your checkout stays untouched. Retain
   scripts, commands, output, inputs, and environment limits. A probe confirms
   an observation; the contract determines whether it is a defect.
4. **Check and deliver.** Seek counterevidence, distinguish new and worsened
   defects from unchanged pre-existing behavior, and retain actionable static
   findings. Instrumentation is useful when it observes a real failure. Ask the
   author only about material missing intent or facts. Return ranked findings
   under `## Defects`, with evidence and relevant questions. A material
   pre-existing defect that a probe executed goes under `## Outside the change`.
   A confirmed consequence that occurs only at the head, through a public
   entry point, where a consumer sees it, is a defect, and so is a failure
   the base handled and the head does not. One whose materiality
   depends on an unverifiable scale or configuration goes under
   `## Minor observations`. The findings are
   saved as `findings.md`. A later search of the same base and head lists the
   earlier findings it did not report again, marked as not rechecked, so
   repeated searches add up. Each search works in its own folder and opens
   the earlier list only after its own findings are settled, so it stays
   independent. Detailed drops and
   tool logs stay in the investigation notes.

Dependency checks use the project's supported-version commands, constraints,
and resolver in a fresh environment.

The remaining-share helper reads the thorough search's candidate table. It
exits 1 while a candidate has no decision or a drop names no allowed ground.
With `--finders`, it also estimates, from how many finders returned each
delivered candidate, what share of what such reads find this search found
(the bias-corrected Chao2 estimator). The estimate holds only for finders
with the same assignment, so the thorough search leaves it out. The
failure-point helper lists the added lines that open, read, write, close,
rename, delete, lock, spawn, or connect; the lead uses the count to decide
whether the fault finder runs.

The static-delta helper runs a type checker or linter command in an exported
copy of two commits and prints the diagnostics the head has and the base
lacks, with file positions ignored. Give it the package and the code that uses
the package, such as tests and documented examples: a package can check clean
while a consumer of its changed types does not. It exits 1 when it prints a
diagnostic, reports each copy's exit status, and leaves the checkout untouched.
A copy holds only committed files; `--link <path>` links what the checker
needs beyond them, such as installed dependencies.

The optional coverage helper reads two committed revisions and an existing
coverage report. It reports executed, missing, excluded, and unclassified added
lines. Coverage paths must match the repository root, without suffix guessing;
missing reports or Git failures produce an error. Istanbul/Vitest results cover
statement starts, not every line of multiline statements. The caller checks
that the report belongs to the inspected source and environment.

Prompt shape:

```text
/aantoniadis-skills:find-bugs <PR URL, branch, or "the working tree"> <"thorough" for several reads> <anything the finder should know>
```

`pr-review-guide` and `check-acceptance` call it as a helper for their search for
bugs; the returned list becomes bug cards, linked from the guide's *you decide*
and *check it* items or from the acceptance report's requirement rows.
Unobserved base/head results remain labeled predictions. A passing diagnostic
can establish the predicted observation while exposing a defect; the check's
result and the finding's status are separate. The calling skill owns integration.


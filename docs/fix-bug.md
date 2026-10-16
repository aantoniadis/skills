# fix-bug

Fix a reported bug with a demonstrated reproduction, a pinned cause, a
regression test that went red then green, and a diagnosis note with an HTML
page a reviewer can verify.

## How it works

1. **Kickoff and contract.** A kickoff round asks the choices the prompt
   leaves open: fix or diagnosis only, HTML or text, working tree or commit.
   Before any fix, the skill pins what should happen, from the failing
   assertion, a plan decision, the issue, documentation, or the intent of the
   commit that wrote the code. A symptom that matches the contract is recorded
   as a mismatch, not fixed; an open behavior decision goes to `plan-change`.
2. **Reproduce.** One saved command goes red on the exact symptom: the failing
   test, a loop built from the issue's steps, or a loop inferred from logs.
   The loop is minimised until every element is load-bearing. Reading code may
   start at once; a red still comes before any cause claim.
3. **Find the cause.** Three to five falsifiable hypotheses, probed cheapest
   first, in parallel through native delegation when more than one survives.
   The cause is a line, a trigger, and the contract it violates; the others
   are recorded as contradicted or unresolved.
4. **Trace origin and reach.** Before anything lands: origin bisects with the
   loop and quotes the breaking commit's intent, to choose a revert or a
   forward fix; reach lists every caller and copied pattern the fix must
   cover. Each runs when the evidence calls for it, and the note says when one
   was skipped and why.
5. **Fix and prove it.** The regression test is written first at a seam that
   exercises the real pattern and watched red; the fix lands at the cause for
   every affected caller and the test is watched green; the original loop
   reruns. With no correct test seam, the note records the gap and keeps the
   loop as proof. When the fix changes a shared producer, its other consumers
   are compared.
6. **Record and deliver.** `diagnosis.md` and `diagnosis.html` at the
   investigation location, checked by `render_page.py`; runs under
   `runs/bugs/<n>/`; the fix and test in the working tree unless a commit was
   authorized; the `visual-pr` command handed over when an applied fix is ready
   for a PR.

Diagnosis only runs steps 1 to 4 and leaves application code and tests
unchanged: the note lists affected callers as unfixed and any fix as a
proposal. With logs or a trace and no loop after a real attempt, the note
delivers ranked hypotheses labeled inferred, the probe that would settle each,
and the fix as a proposal; a fix lands without a red only when you authorize
it.

Prompt shape:

```text
/aantoniadis-skills:fix-bug <the symptom: a failing test, a CI link, an issue, or a log excerpt> <what should happen, if known>
```

## Invocation beside other debugging skills

Matt Pocock's `diagnosing-bugs` and superpowers' `systematic-debugging` also
fire on "fix this bug". Both run a reproduction loop; `fix-bug` adds the
contract, origin, reach, consequence, and record. In trigger tests with both
installed, the host selected `fix-bug` for every bug report. If another
debugging skill starts instead, invoke `fix-bug` by name, or disable the
overlapping skills in the projects where you want this workflow. Started
inside another discipline, the skill continues under its own steps.

# Diagnosis pages

Read this when filling or rendering a diagnosis note. Use the [shared page
workflow](../../HTML-PAGES.md) to fill [diagnosis-template.md](diagnosis-template.md)
and render it; this file says what each section is for and which page
components carry it. Every claim keeps the floor of [EVIDENCE.md](../../EVIDENCE.md):
a pinned line, an observation, a quote with its link, or an explicit label.
The checker applies that floor per paragraph and per table row, so Where,
Trigger, and Who / impact stay separate paragraphs, each with its own evidence.

## Reading order

- **Verdict:** the symptom, the contract, the cause, and the fix state in one
  paragraph a reviewer reads in 30 seconds, each with its deciding pin or run
  link. The **Checked** line carries six chips, one per family value of the
  diagnosis checks key (*reproduced* or *not reproduced*; *fixed*, *fix
  proposed*, or *no fix proposed*; *test red then green*, *test not verified*,
  or *no test seam*; then origin, reach, and consequence as *checked* or
  *skipped*), each followed by its reason or result. Use *test not verified*
  when red-to-green evidence is incomplete, including diagnosis-only work;
  an unrun or still-red test does not imply a missing seam.
  Use *fix proposed* for a direction or diff; *no fix proposed* means neither
  was offered and no fix was applied.
  When the loop ran against a stand-in for the component that carries the
  bug, follow *reproduced* and *test red then green* with ", on a model of
  <component>".
- **Symptom and contract:** the report quoted from its source, then what
  should happen with its source, then the verdict. A "works as specified"
  verdict ends the note here with the mismatch; an open behavior decision
  names the question and the owner. Omit inapplicable fix and test chips for
  these verdicts.
- **Reproduction:** the loop command as a fence, its output line, the four
  criteria as a table with evidence, and what minimisation cut. The
  artifacts-only branch replaces the command with what was tried and the
  access or artifact that would give a loop.
- **Cause:** the decisive excerpt as a code card (a fence whose info string
  carries `url="<pinned link>"`), then one `### 1.` card named by what the
  cause does. The card opens with two chips, the evidence chip (*we ran it* or
  *suspected, not run*) and the cause origin chip (*regression*, *always
  broken*, or *origin not checked*), then Where, Trigger, Who / impact as
  labeled paragraphs and the Before/After table. The page frames it like a
  review's bug card.
- **Hypotheses:** the table with every hypothesis named by what it says, its
  prediction, its probe, and its verdict.
- **Origin, Reach, Consequence:** each either carries its result with evidence
  or one sentence saying it was skipped and why.
- **Fix and regression test:** an applied or proposed diff, when available,
  then the test's seam and actual run state. Diagnosis-only work records the
  cause and optional fix direction without requiring a patch or green run.
  The page renders a `diff` fence side by side with the unified diff beneath it.
- **Verification:** the shared table; executed rows link their run record in
  the first cell, and a proposed check says Not run / Proposed.
- **Limits and next steps, Next step, Evidence and record:** what stays open,
  where the fix sits and the next command, and the provenance.

## Components and limits

A diagram is optional: a short flowchart of callers into the cause helps a wide
reach; the sentence before the fence states its evidence kind and a source map
follows it, as [EVIDENCE.md](../../EVIDENCE.md) says. Keep hypotheses, probes,
and runs named in plain words; numbered IDs stay in the run record. Secrets are
redacted in every fence and output line. The note is authoritative; the page
reorganizes nothing that changes a finding, a condition, or an evidence label.

## What the checker enforces

`render_page.py --check` names each failing line and the rule it broke; repair
from its message. The rules a diagnosis note meets most often:

- Every paragraph, list item, and table row that makes a claim carries a
  pinned line, a link to a run record, a quote with its link, or an evidence
  label such as *observed*, *inferred*, *proposed*, or *not run*. Sections
  about scope, provenance, the record, and next steps are exempt.
- In Verification, *Passed*, *Failed*, and *Mixed* pair with *Executed here*
  or *Recorded run* and a run-record link in the first cell; *Source
  inspected* pairs with *Not run*; *Proposed* pairs with *Not run* or
  *Blocked*. Every cell is filled.
- The first line under the cause's `### 1.` heading is the two chips and
  nothing else. The Checked line uses values from the diagnosis checks key.
- Hypotheses, probes, and runs are named in words; IDs such as H1 or R2 fail.
- The `## Status and label key` section is generated: `--sync-labels` writes it.

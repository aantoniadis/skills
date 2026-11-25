# Proposing the rework

Read when turning the findings into targets and steps. The proposal names
every move exactly, because a rework that states its target is carried out
well, and one that says "clean this up" produces renames.

## Contents

- [Group the findings](#group-the-findings)
- [Offer targets](#offer-targets)
- [Order the steps](#order-the-steps)

## Group the findings

Sort the findings under the change that removes them. Work out each change as
if the system had known today's requirements from the start: one change often
removes several findings that look unrelated, and it often looks like none of
them. Keep a grouping only when, after it:

- pieces that change together sit together;
- pieces that change for different reasons are no longer tied;
- dependencies point toward the code that changes less;
- the rule has fewer decision sites than before. Count them.

A structure finding that no change removes at an acceptable cost is listed as
kept, with the cost that decided it.

## Offer targets

Describe the recommended target in full, and each alternative in a few
sentences: what it changes, what it costs, and why it is not the
recommendation. One alternative always leaves the structure as it is, with
what that costs at the present rate of change. Add another only when it is
materially different and you would defend it to the user.

When the findings do not justify a restructuring, the recommendation is to
leave the structure as it is. The proposal is then short: the pins for the
behavior no test protects, the corrections to documents that state something
the code does not do, and the check that locks the stated design in.

For the recommended target, state:

- **Owners.** For each rule and each piece of state in the findings, the one
  module that decides or writes it. Prefer the module that already holds the
  data the rule reads.
- **Interface.** What callers need to know, as signatures or types. The right
  shape removes branches and states that cannot be valid; a shape that adds
  indirection and removes neither is surplus.
- **Guarantees at the boundary.** What is checked once where data enters, and
  the inner checks that become unnecessary as a result. List them by line.
- **Failure behavior.** For each fallback and each error turned into a value
  in scope: the failure cannot occur under the new shape, or it fails loudly,
  or it is a real outcome the caller receives. Each one that changes what a
  consumer sees is behavior to decide, not part of the target.
- **Cost and risk.** Files and call sites touched, the pins that exist and the
  pins to write, and what can go wrong.
- **Measure.** Decision sites per rule before and after, and the stated
  dependencies and rules that become true.

Rank by where change is paid: a target that concentrates a rule changed every
week is worth more than one that tidies code nobody touches. Give one
recommendation and its reason. When the project keeps decision records, offer
the chosen target, and each rejected target that has a lasting reason, as a
record, so that a later run does not propose the rejected one again.

## Order the steps

Write the steps for the chosen target, or for the recommended one while the
choice is open. Each step is small enough to review alone and leaves the
component working. Order them:

1. **Pin.** For each behavior a later step moves, name the existing test that
   pins it, or the characterization test to write at a seam: a test that
   records what the code does today. The [deliberate breaks](census.md#a-deliberate-break)
   of the census say which behaviors have a pin already, and a probe from the
   census is the starting point of a new one. Each pin is seen failing once
   against a deliberate break, because a pin never seen to fail may assert
   nothing. A green suite, a type check, or a lint run is not a pin.
2. **Subtract.** Remove what the map showed as surplus and what
   [special cases](special-cases.md) allows removing. Less code makes every
   later step smaller.
3. **Gather.** Move each scattered rule to its owner, one rule per step,
   updating every decision site in that step.
4. **Reshape.** Change the model or interface the target names, with every
   caller migrated in the same step. Keep a compatibility path only for a
   consumer outside the repository: a deployed client, stored data, a public
   interface.
5. **Lock in.** Express the target's allowed dependencies as a check the
   project runs, with the ecosystem's dependency-rule tool or the stated
   design file and `design_conformance.py`, so that the next change cannot
   quietly undo the rework.

Write every step with:

- its kind, *structural*. A step that would change behavior is not a rework
  step: it belongs under behavior to decide. A step that holds only under one
  answer to an open question is listed as waiting for that answer;
- the files it touches, and every call site of a moved or changed symbol,
  enumerated with a resolver. Call sites left behind are the most common
  failure of a rework across files;
- its pin;
- its proof that behavior is unchanged: the pins green, and for a step that
  moves a decision, the old and the new output compared on the same inputs.
  A step that changes only a document or a check has no pin; its proof is the
  check itself.

The steps are a plan. Carrying them out is a separate task that the user
starts, through [plan-change](../../plan-change/SKILL.md) for the whole
rework, or directly for one contained step.

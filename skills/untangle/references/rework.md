# Proposing the rework

Read when turning the findings into targets and steps. The proposal names
every move exactly, because a rework that states its target is carried out
well, and one that says "clean this up" produces renames.

## Group the findings

Sort the findings under the change that removes them. Work out each change as
if the system had known today's requirements from the start: one change often
removes several findings that look unrelated, and it often looks like none of
them. Keep a grouping only when, after it:

- pieces that change together sit together;
- pieces that change for different reasons are no longer tied;
- dependencies point toward the code that changes less;
- the rule has fewer decision sites than before. Count them.

A finding that no change removes at an acceptable cost is listed as kept, with
the cost that decided it.

## Offer targets

Describe two or three materially different targets. One of them leaves the
code as it is, with what that costs at the present rate of change. For each
other target, state:

- **Owners.** For each rule and each piece of state in the findings, the one
  module that decides or writes it. Prefer the module that already holds the
  data the rule reads.
- **Interface.** What callers need to know, as signatures or types. The right
  shape removes branches and states that cannot be valid; a shape that adds
  indirection and removes neither is surplus.
- **Guarantees at the boundary.** What is checked once where data enters, and
  the inner checks that become unnecessary as a result. List them by line.
- **Failure behavior.** For each fallback and swallowed error in scope: the
  failure cannot occur under the new shape, or it fails loudly, or it is a
  real outcome the caller receives. Each one that changes what a consumer sees
  is a question for the user.
- **Cost and risk.** Files and call sites touched, the pins that exist and the
  pins to write, and what can go wrong.
- **Measure.** Decision sites per rule before and after, and the relationships
  that become *as stated*.

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
   records what the code does today. A probe from the census is its starting
   point. Each pin is seen failing once against a deliberate break, because a
   pin never seen to fail may assert nothing. A green suite, a type check, or
   a lint run is not a pin.
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
  step: list it as a decision for the user;
- the files it touches, and every call site of a moved or changed symbol,
  enumerated with a resolver. Call sites left behind are the most common
  failure of a rework across files;
- its pin;
- its proof that behavior is unchanged: the pins green, and for a step that
  moves a decision, the old and the new output compared on the same inputs.

The steps are a plan. Carrying them out is a separate task that the user
starts, through [plan-change](../../plan-change/SKILL.md) for the whole
rework, or directly for one contained step.

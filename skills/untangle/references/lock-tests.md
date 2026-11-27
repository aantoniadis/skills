# Lock tests

Read when writing the tests that lock today's behavior before a rework. A
lock test records what the code does now, not what it should do. Its job is
to fail when a rework step changes a result, so that the change is a decision
someone makes on purpose instead of a side effect nobody sees.

## Contents

- [List what to lock](#list-what-to-lock)
- [Choose the seam](#choose-the-seam)
- [Choose the inputs](#choose-the-inputs)
- [Name and mark it](#name-and-mark-it)
- [See it fail](#see-it-fail)
- [Record](#record)

## List what to lock

Start from each step of the chosen target, not from the spec alone. A
behavior marked *tested* can lose its test to the step itself:

- **Tests the step deletes.** For each test that goes through code the step
  removes, name what it pinned that the step keeps, and lock that on the
  path that stays. A gate tested only through a fallback is untested once
  the fallback goes.
- **A copy that becomes the only one.** When a step removes one of two
  places that decide the same thing, the one that stays needs its own test:
  until now the other answered for it.
- **Call sites the step edits.** When a step changes what each caller
  passes, such as an argument that becomes required, lock each entry point
  with a test that fails when that caller passes another value. A probe
  that calls the owner directly proves the owner, not the callers.
- **A default the step makes permanent.** When a step removes the path that
  treated a missing declaration or value differently, lock what the default
  gives, or that nothing relies on it.

A behavior with no test after this is listed in the map as a gap, with what
writing its test needs.

## Choose the seam

Write each test against an interface the chosen target keeps: a public
function, an endpoint, a command, a job, a message handler. A test written
against a helper the rework deletes or moves breaks with the refactoring and
locks nothing.

- Prefer the highest seam that runs fast and gives a deterministic result.
  One test through an endpoint can lock what three internal helpers decide
  together.
- Where several entry points decide the same rule, lock each one: the
  rework gathers them, and each must keep its result.
- Where the result is large or hard to state, such as a document, a report,
  or a response body, record the whole of it in a file beside the test and
  compare against it (an approval or golden-master test). Remove values that
  change from run to run, such as timestamps, ids, and ordering of unordered
  sets, before comparing.
- Where state is the result, such as a stored row or a written file, assert
  the state after the call, not only the return value.

## Choose the inputs

Take the inputs from what the census ran: each probe, each scenario that
reached a decision site, each case a deliberate break showed unprotected.
Add the inputs that sit on the edges of a rule: each value of the
discriminator, a missing value, the boundary of a threshold. Keep the set
small enough to read; a lock test is documentation as well.

Choose an input for which the broken code gives another result. When a
later branch or a fallback returns the same result for the input, the test
cannot fail: an order with no discount has the same total whether the
discount branch runs or not, so the test of that branch needs an order that
has one.

## Name and mark it

Name each test after the behavior it locks, in domain words. Group the lock
tests where the project keeps tests for that interface, or in one file named
for the rework when the project has no better place, and say at the top of
that file what they are for.

A test that records a result listed under behavior to decide, such as two
entry points that disagree, still asserts today's value. Its name says it
records a value under decision, and a comment links the map's question, so
that answering the question changes the test deliberately.

## See it fail

A test never seen to fail may assert nothing. For each test, in a disposable
worktree as [census](census.md#a-deliberate-break) says, with
`break_probe.py --with-local-changes`, which brings the uncommitted tests
into the worktree:

1. Make the change the test is meant to catch: alter the decision it locks.
2. Run the test, and record the break and the failure. Read the failure in
   the log: a red counts only when it is the lock test's own assertion. An
   error the break itself causes, such as a syntax error or a file that no
   longer loads, pins nothing.
3. Restore, and run it again green.

Then run the whole suite on the unchanged code and record it green. A test
that stays green under its break is rewritten at another seam, or its gap is
recorded in the map.

## Record

List the lock tests under *Lock tests* in the map's plan: the test, the
behavior it locks, the break it failed under with the run, and the suite run
that passed. The rework steps name these tests as their pins. Lock tests
move the lines of the test files they join, and the map's pins stay at the
inspected revision: cite a lock test by its name, and say once which lines
moved.

# Lock tests

Read when writing the tests that lock today's behavior before a rework. A
lock test records what the code does now, not what it should do. Its job is
to fail when a rework step changes a result, so that the change is a decision
someone makes on purpose instead of a side effect nobody sees.

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
worktree as [census](census.md#a-deliberate-break) says:

1. Make the change the test is meant to catch: alter the decision it locks.
2. Run the test, and record the break and the failure.
3. Restore, and run it again green.

Then run the whole suite on the unchanged code and record it green. A test
that stays green under its break is rewritten at another seam, or its gap is
recorded in the map.

## Record

List the lock tests in the map's *Lock tests* section: the test, the
behavior it locks, the break it failed under with the run, and the suite run
that passed. The rework steps name these tests as their pins.

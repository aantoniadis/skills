# Thorough search

Read this when the user or the caller asks for a thorough search. Four or
five finders read the change independently: one general finder and three or
four finders with their own focus. You run the shared tools once, merge what
the finders return, record a decision for every candidate, and confirm each
delivered candidate once. A thorough search costs several times one read.

## Contents

- [Start the finders](#start-the-finders)
- [Run the shared tools once](#run-the-shared-tools-once)
- [Decide every candidate](#decide-every-candidate)

## Start the finders

First run `python3 <package>/skills/find-bugs/scripts/failure_points.py --base <base> --head <head> --repo <checkout>`.
It lists the added lines that open, read, write, close, rename, delete, lock,
spawn, or connect.

Then, through [native delegation](../WORKERS.md), start the finders in one
message: a general finder, a consumers finder, an inputs finder, a state
finder, and, when the list has five or more lines, a fault finder. With fewer lines, skip the fault
finder: make each listed line fail once yourself in step 3, and record that.
Wait for every finder's result before step 3. Give each this assignment and
nothing from your own reading or the shared tools; a finder that knows what
was found looks where the others looked:

> You are one of several independent finders for one change. You do not see the others' work. Repository: `<path>`. Base: `<sha>`. Head: `<sha>`. Conditions: `<dependency and environment notes from step 1>`. Work in `<this search's folder>/finder-<focus>/` and leave the checkout unchanged. Follow steps 2 and 3 of `<package>/skills/find-bugs/SKILL.md` for this change as one read: search alone and start no workers. The lead runs the static deltas, `weakened_checks.py`, and the base's tests for this search, so begin with the reading. Run code when running it is how you find out, because the source leaves the outcome open: inject a failure, force an interleaving, try an input, or compare base and head on a scenario you suspect. Save each probe you run with its command and result. When the source already shows the outcome, return the candidate as *inferred* with the probe that would show it; the lead confirms each distinct candidate once. Return every candidate you could not contradict: location, trigger, base result, head result, the contract it breaks, and the saved probe, or *inferred* with the probe to run. List the leads you dropped, one line each with the counterevidence. Do not rank or write a report.

The general finder gets the assignment as it stands; it catches what falls
outside the focuses. Each focused finder also gets the paragraph for its
focus.

The **consumers finder**: *Search only what code outside the change sees.
List the callers of each changed function; the subclasses and overrides of
each changed class; the callbacks and hooks that users supply; the generic
protocols that users apply to changed objects, such as copy, pickle, equality,
and iteration; and the docs, examples, and type declarations that describe the
changed code. For each, compare what it receives or observes at the base and
at the head.*

The **inputs finder**: *Search only the values that the changed code now
treats differently: None, empty, boundary, and malformed arguments; each
default; each option that the changed path reads or now ignores, alone and
combined with the others; and each runtime, operating system, and filesystem
that the project supports. For each value, compare the base and head results.*

The **state finder**: *Search only the state this change adds or shares:
caches, lazy initialization, counters, and containers that outlive one call.
For each, probe what two threads or tasks see when they reach it at once, and
what a reader sees after it changes.*

The **fault finder**: *Search only what happens when the outside world does
not cooperate. `python3 <package>/skills/find-bugs/scripts/failure_points.py --base <base> --head <head> --repo <checkout>`
lists the added lines that open, read, write, close, rename, delete, lock,
spawn, or connect. Make each one fail in turn, part-way through the change's
sequence, with an error that call can raise, and record what remains: open
descriptors, partial or orphaned files, a flag or counter still set, and the
error type the caller sees against the one the code documents. Then give each
path the change opens or creates what another process or account could leave
there: a directory, a symlink, a file owned by another user, a file without
read permission. Report a candidate only when the base handled the same
condition, or when the change documents how it handles it.*

Where no delegation tool is available, as can happen
for a worker, search once yourself and say so in the delivery.

## Run the shared tools once

While the finders run, run these yourself, once for the whole search. Each
result you keep is a candidate from finder `lead`.

- The static deltas, as step 2 says.
- `weakened_checks.py`, as step 2 says.
- The base's tests against the head. In a disposable worktree at the head,
  restore the test files that the change edits or deletes to their base
  versions: `git -C <worktree> checkout <base> -- <test files>`. Run those
  files. A test that passes at the base and fails there pinned a behavior that
  the change altered. Skip this when the change edits no test file, and record
  that.

## Decide every candidate

Write `candidates.md` in this search's folder, one row for each candidate that
a finder or a shared tool returned:

```markdown
| Candidate | Finders | Disposition |
|---|---|---|
| release() blocks a waiting acquire | consumers, state | delivered |
| same, through release(force=True) | inputs | merged into release() blocks a waiting acquire |
| lifetime warning text | consumers | dropped: same at base: base prints the same text, probe p3 |
| duplicate pool for an encoded host | inputs | delivered |
```

A disposition is `delivered`, `merged into <candidate>`, or a drop that names
one of three grounds and then the evidence for it:

- `dropped: absent at head: <source line or probe result>`
- `dropped: same at base: <source line or probe result>`
- `dropped: documented intent: <the text in the change that documents it>`

Merge candidates that share a location and mechanism, keep every distinct
trigger, and list a merged row's finders on the row it merged into. A
candidate from one finder is as likely real as one from several: confirm it
in step 3, do not vote. A small consequence is not a ground for a drop: a
behavior that the head shows and the base does not stays `delivered`, and you
deliver it under `## Minor observations`, naming why it is minor.

Then run `python3 <package>/skills/find-bugs/scripts/remaining.py <this search's folder>/candidates.md`.
It exits 1 while a row has no disposition or a drop names no allowed ground.

Done when every finder has returned or is recorded as *not run* with its
reason, each shared tool ran or has a recorded reason, each listed failure
line failed once when no fault finder ran, and `remaining.py` exits 0.

# Thorough search

Read this when the user or the caller asks for a thorough search. Five finders
read the change independently; you merge what they return, record a decision
for every candidate, and verify. A thorough search costs about six times one
read.

## Start the finders

Through [native delegation](../WORKERS.md), start five finders in one message:
three general finders, one state finder, and one fault finder. Wait for all
five results before step 3. Give each this assignment and nothing from your
own reading; a finder that knows what was found looks where the others looked:

> You are one of several independent finders for one change. You do not see the others' work. Repository: `<path>`. Base: `<sha>`. Head: `<sha>`. Conditions: `<dependency and environment notes from step 1>`. Work in `<this search's folder>/finder-<n>/` and leave the checkout unchanged. Follow steps 2 and 3 of `<package>/skills/find-bugs/SKILL.md` for this change as one read: search alone and start no workers. Return every candidate you could not contradict: location, trigger, base result, head result, the contract it breaks, and the saved probe with its command, or *inferred* with the missing probe. List the leads you dropped, one line each with the counterevidence. Do not rank or write a report.

The **state finder** gets one more sentence: *Search only the state this
change adds or shares: caches, lazy initialization, counters, and containers
that outlive one call. For each, probe what two threads or tasks see when they
reach it at once, and what a reader sees after it changes.*

The **fault finder** gets one more paragraph: *Search only what happens when
the outside world does not cooperate. `python3 <package>/skills/find-bugs/scripts/failure_points.py --base <base> --head <head> --repo <checkout>`
lists the added lines that open, read, write, close, rename, delete, lock,
spawn, or connect. Make each one fail in turn, part-way through the change's
sequence, with an error that call can raise, and record what remains: open
descriptors, partial or orphaned files, a flag or counter still set, and the
error type the caller sees against the one the code documents. Then give each
path the change opens or creates what another process or account could leave
there: a directory, a symlink, a file owned by another user, a file without
read permission. Report a candidate only when the base handled the same
condition, or when the change documents how it handles it.*

When no failure point is listed, start the fault finder anyway: the list finds
leads, not every call.

While the finders run, run the static deltas yourself. Where no delegation
tool is available, as can happen for a worker, search once yourself and say so
in the delivery.

## Decide every candidate

Write `candidates.md` in this search's folder, one row for each candidate any
finder returned:

```markdown
| Candidate | Finders | Disposition |
|---|---|---|
| release() blocks a waiting acquire | 1, 3 | delivered |
| same, through release(force=True) | 2 | merged into release() blocks a waiting acquire |
| lifetime warning text | 4 | dropped: base prints the same text, probe p3 |
```

A disposition is `delivered`, `merged into <candidate>`, or
`dropped: <counterevidence>`. Merge candidates that share a location and
mechanism, keep every distinct trigger, and list a merged row's finders on the
row it merged into. A candidate from one finder is as likely real as one from
all five: verify it in step 3, do not vote. Drop one only with the source line
or probe result that contradicts it.

Then run `python3 <package>/skills/find-bugs/scripts/remaining.py --finders 5 <this search's folder>/candidates.md`.
It exits 1 while a row has no disposition. Its last line estimates what share
of the defects that reads of this kind find this search found: many candidates
seen by one finder only mean another thorough search would add more. State
that share in the delivery as a rough figure, and say that it does not count
defects no read of this kind reaches.

Done when every finder has returned or is recorded as *not run* with its
reason, and `remaining.py` exits 0.

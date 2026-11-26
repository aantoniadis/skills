# Special cases

Read when classifying a guard, default, error turned into a value, retry,
compatibility path, or single-caller parameter, and before proposing to remove
one. Two
facts decide each case: whether anything reaches it, and why it exists. An
unexplained special case is evidence about the design before it is a line to
delete.

## Contents

- [Which ones to account for](#which-ones-to-account-for)
- [Reach](#reach)
- [Why it exists, and what it points to](#why-it-exists-and-what-it-points-to)
- [When it bends the design](#when-it-bends-the-design)
- [Before proposing a removal](#before-proposing-a-removal)

## Which ones to account for

Start from the list [`special_cases.py`](../scripts/special_cases.py) prints,
and add what reading finds: the script has no pattern for a clamp, for a
parameter one caller sets, or for a retry written without the word.

```bash
python3 <package>/skills/untangle/scripts/special_cases.py --summary <scope>   # counts per kind and file
python3 <package>/skills/untangle/scripts/special_cases.py <scope>             # every line
```

Give a row in the map to every broad error handler, retry or sleep, and
compatibility path in scope, and to every error turned into a value, default,
early return, and status or version branch that sits on a decision site of
the census: those decide what a consumer sees. Count the rest per kind and
file, and label them *not inspected* one by one. In code whose job is to
translate errors, such as a client for another service, most handlers are the
main path; say so once and classify the ones that differ from the pattern.

## Reach

Establish reach from several kinds of evidence, because each kind alone fails
in a known way:

| Evidence | What it shows | What it does not show |
| --- | --- | --- |
| Callers and types | Whether any producer can create the state the case handles. | Producers behind reflection, injection, external callers, or stored data. |
| A reach probe | A script that drives an input through the public boundary to the case. A probe that reaches it settles the question. | A probe that fails to reach it shows only that this input did not. |
| A removal probe | In a scratch worktree, delete the case and run the baseline suite. A test that turns red names what depends on the case. | A green suite shows that no test pins the case. Production may still reach it. |
| Production signal | A log line, metric, or error report from the branch, when the project has one. | Anything outside the retained window. |
| History | `git blame -w -C` on the line, then `git log -S'<its text>'`: the commit, ticket, or incident that added it. | Whether the reason still holds. |

Run a removal probe as [a deliberate break](census.md#a-deliberate-break): in
a disposable worktree, delete the case and run the baseline.

Record each case with one reach status:

- *reached*: a named caller, input, test, or run reaches it. Cite it.
- *not reached*: the callers are enumerated and none produces the state, and a
  reach probe through the public boundary failed. State both.
- *unknown*: anything else, including a case that only lacks test coverage.

## Why it exists, and what it points to

Take the reason from history first. Ask the user when history gives none, or
when the reason may no longer hold. Then name what the case points to:

- **A missing requirement.** The situation is real and the design never
  accounted for it, so one site handles it alone. The finding is the
  requirement, and the rework gives it an owner.
- **A producer emitting a state it should not.** The check sits where the
  symptom appeared. The finding is the producer; a check that hides the state
  hides the defect, which goes to [fix-bug](../../fix-bug/SKILL.md).
- **An implicit boundary.** Inner code re-checks what an outer layer already
  guarantees, because nothing states the guarantee. The finding is the
  boundary: checked once where data enters, the inner checks become surplus.
- **A real outcome.** The failure is part of the domain, such as "the remote
  service is down". It belongs in the return type or the error the caller
  sees, and the question for the user is what the consumer should see.
- **Nothing found.** No producer, no reason in history, and the user knows
  none. It is an unjustified special case.

## When it bends the design

A *reached* case can still cost more than it is worth: a flag passed through
layers, a branch in the general path, or state kept only for it. Weigh it as
[corner cases](../../CORNER-CASES.md) says, with its own card in the map, and
let the user choose between keeping it, isolating it, and rejecting the case.

## Before proposing a removal

Propose removing a special case only when one of these holds, and say which:

- Its status is *not reached*, history gives no reason that still holds, and
  the user agrees, or a production signal shows it silent over a stated window.
- It duplicates a check that demonstrably runs earlier on every path to it:
  cite the earlier check and the paths.

These stay, whatever their coverage:

- A check at a trust boundary: user input, an external service, stored data,
  file and network operations, authorization, protection against data loss.
  To propose removing one, first write an adversarial probe, with malformed or
  hostile input, that fails without the check. With no such probe, it stays.
- A handler on a path that must finish whatever fails: cleanup, shutdown,
  disconnect, a fire-and-forget operation whose failure the caller does not
  need. Narrow it to the errors it expects when it catches everything.
- A case whose status is *unknown*. Unexecuted means untested; it does not
  mean unreachable.

A fallback that returns a value in place of a failure changes what the
consumer sees. Removing it, or making it fail loudly, is a behavior change:
record the current result from a run that triggers it, and list the wanted
behavior as a question for the user.

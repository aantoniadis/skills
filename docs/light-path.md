# The light path

For a contained change, establish the outcome, implement within scope, run useful
checks, and review the result. Use the steps that the task needs. Existing project
conventions and settled decisions carry forward; a small change does not need a
new interview, spec, tool setup, or separate agent session by default.

Use [explain](../skills/explain/SKILL.md) for a factual gap and
[plan-change](../skills/plan-change/SKILL.md) for consequential unresolved behavior.
Unfamiliar code or a sensitive boundary warrants focused investigation; it does
not automatically require every stage of the [complete workflow](workflow.md).
Schema changes, external consumers, shared state, and irreversible operations
need their relevant compatibility, failure, and recovery questions settled.

## 1. Establish the outcome

Reuse the request, ticket, or existing plan. Identify the observable result,
relevant behavior to preserve, and scope. Investigate code facts directly. Ask
only about consequential choices the available context or an authorized decision
policy does not settle. An unresolved choice blocks its dependent work; continue
independent work when useful.

When a short spec helps, keep it at the selected project location. It can contain:

```markdown
# <Change>

## Outcome
Who needs this and the observable result.

## Acceptance
- Given <condition>, when <action>, then <outcome and consumer response>.

## Preserved behavior and scope
- <Relevant invariant and excluded work>.

## Decisions and assumptions
- <Named decision>: <choice and reason>; authority: <answer or authorized policy>.
- <Open assumption>: <what remains unknown and affected work>.

## Remaining questions
- <Consequential question and dependent work, or none>.
```

Routine coding choices remain with implementation. A default is an assumption
unless the user or an explicitly authorized policy settles it. Record decisions
that affect behavior, contracts, or later work; a full choice ledger is unnecessary.
For a difficult interview, the original `mattpocock:grilling` is invoked
through the host, as [package references](../skills/REFERENCES.md) say, when
explicitly selected.

## 2. Choose useful checks

Use the project's existing checks and the acceptance conditions. Add or update
focused tests where they provide useful regression evidence. One test may cover
several conditions; select cases by consequence rather than enforcing a one-to-one
count. Separate inspected assertions, recorded runs, and fresh executions.

Use TDD or a separate test author when the user or project selects that
practice. These are options, not requirements for every
small change. If a test or its setup fails, determine whether that establishes
product behavior or only an environment gap.

## 3. Implement

Implement the authorized change with the host's usual coding workflow. A new
session or upstream implementation skill is optional. If selected, hand off to
`mattpocock:implement` as [package references](../skills/REFERENCES.md) say:
the user runs it with the scope, agreed behavior, and applicable evidence; its
original workflow commits changes, so the command carries the user's actual
commit boundaries.

Resolve routine implementation choices using project conventions. Reopen a
consequential decision when new evidence affects it, and pause only dependent
work. Preserve earlier observations and record corrections without rewriting the
original results. Fix a mistaken test within existing task authority; if it
changes agreed acceptance behavior, resolve that choice first.

## 4. Run project checks

Run the checks appropriate to the change and report results, conditions, and
remaining gaps. Use
[find-bugs](../skills/find-bugs/SKILL.md) when a focused defect investigation would
help, especially around lifecycle, concurrency, error paths, or compatibility.
The skill reports findings; application fixes stay within the implementation task.
A failing check whose cause is unknown is a bug report:
[fix-bug](../skills/fix-bug/SKILL.md) reproduces it, pins the cause, and leaves
the fix with its regression test and diagnosis note.

## 5. Review and deliver

Compare the implementation with the intended outcome, preserved behavior, and
actual checks. Focus review depth on consequential changes and evidence gaps.
Use [pr-review-guide](../skills/pr-review-guide/SKILL.md) when a reusable human PR
guide helps.

Deliver the result and relevant limits. Create or update a PR only within the
user's publication authority. Include enough intent and evidence for its readers;
a local scratch link alone does not make that evidence accessible remotely.

When rework reveals a recurring omission, propose the smallest useful improvement
to a question, project convention, or check. Update project instructions only
within a task that authorizes those edits.

# fit-change

Keep one change from eroding the design. Before a feature or bug fix is
written, the skill places it: which module owns each rule the change touches,
what existing code it reuses, and whether the structure has to be reshaped
first. After the change, it checks the diff for what was added in a second
place, in the wrong module, or for no stated reason.

It exists because an agent given a ticket takes the shortest path that passes
the tests. It carries out a restructuring well when someone names it, and
rarely chooses one by itself. So the decision about where a rule lives is put
to you, on evidence, before the code is written.

## How it works

**Place**, before the change:

1. **Name what the change decides:** the rules it adds or alters, the state it
   writes, and the failures it can meet.
2. **Find each rule's decision sites today:** every place that decides it,
   from search, references, and the history of its lines. Where two sites
   decide the same rule, the skill runs one input through both.
3. **Test the fit.** The change fits when each rule changes at one site, in
   the module that owns it. It does not fit when the same condition has to
   change in a second file or layer, when the change adds one more branch to
   a chain on the same discriminator, when a value must be threaded through
   layers that do not use it, when a fix would sit at the symptom and not at
   the producer, or when the rule's sites already disagree.
4. **Decide.** A change that does not fit becomes a choice for you,
   recommendation first: reshape first, with behavior-preserving steps and
   the test that pins each, or patch, with what the next change will cost.
5. **Settle failure behavior:** what the request says a consumer sees on each
   failure, or a question for you. Until it is answered, the error propagates.
6. **Write the placement** into the plan or ticket, or as `placement.md`:
   rules and owners, reuse, reshape steps, what is in and out of scope,
   failure behavior, and the check to run afterwards.

**Check**, after the change:

1. **Pin** the base and head and run the tests at the head.
2. **Take leads on the added lines:** the guards, defaults, handlers, and
   retries the change adds, the added lines no test executes, and any
   dependency the stated design does not allow that is new at the head.
3. **Count decision sites, base against head.** More sites for a rule is a
   scattered rule. A decision outside the rule's owner is misplaced logic. A
   rule changed at some sites and not at others is behavior to decide, handed
   to `find-bugs` or `fix-bug` with both results.
4. **Account for every added special case:** its producer and its reason, or
   it is an unjustified special case. A check where data enters the system is
   fine.
5. **Look for added surplus:** a wrapper that only delegates, an option
   nothing sets, an interface with one implementation, a compatibility path
   with no outside consumer, an old path left after its callers moved.
6. **Compare with the placement,** when there is one.

The check reports only these kinds, each with its evidence, and "nothing
found" is a result. When you ask it to apply fixes, a fix deletes, moves, or
reuses; it adds no abstraction, no check, and no test for a state nothing
produces.

Prompt shapes:

```text
/aantoniadis-skills:fit-change <the feature or fix you are about to make>
/aantoniadis-skills:fit-change Check <the branch, PR, or working tree> against <base>. <Report only | Apply the fixes that keep behavior.>
```

## Two rules it applies

- **Restructuring the placement names is in scope. Everything else stays as
  it is.** This is how a change includes the refactoring it needs without
  growing into a rewrite.
- **A check needs a producer; a fallback needs a decision.** A guard is added
  only with the caller, input, or stored value that produces the state. A
  fallback is added only where the request or you say what the consumer
  should see.

## In sessions that do not invoke it

A session that never runs the skill still reads the project's instruction
file. When the same kind of finding appears in a second change, the skill
proposes the matching line for that file, or a check the project runs, from
its [house rules](../skills/fit-change/references/house-rules.md). It prefers
a check for anything mechanical, because an instruction is followed some of
the time and a failing check every time.

## Beside the other skills

| Skill | Looks at | Answers |
| --- | --- | --- |
| `plan-change` | The behavior a change should have | What should happen, and what must stay the same |
| `fit-change` | The structure one change touches | Where the code belongs, and whether to reshape first |
| `find-bugs` | A finished diff | What is wrong in what it does |
| `untangle` | A whole component | How it is built today, and what rework would help |

## Limits

- Finding every decision site of a rule depends on search and references; a
  site under another name, or reached through an injected object, can be
  missed. The placement names the searches it ran.
- The check judges structure. A change can pass it and still be wrong.
- Whether a restructuring is worth its cost is your decision; the skill gives
  the count of sites and the files touched under each choice.

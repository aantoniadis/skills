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
   writes, the failures it can meet, and the modules, classes, or files it
   adds, each with the decision only it makes. One that would decide nothing
   stays out of the placement.
2. **Find each rule's decision sites today:** every place that decides it,
   from search, references, and the history of its lines. Where two sites
   decide the same rule, the skill runs one input through both.
3. **Test the fit.** The change fits when each rule changes at one site, in
   the module that owns it. It does not fit when the same condition has to
   change in a second file or layer, when the change adds one more branch to
   a chain on the same discriminator, when a value must be threaded through
   layers that do not use it, when a fix would sit at the symptom and not at
   the producer, when the change needs one more key in a hash several
   modules read and write, or when the rule's sites already disagree.
4. **Decide.** A change that does not fit becomes a choice for you,
   recommendation first: reshape first, with behavior-preserving steps and
   the test that pins each, or patch, with what the next change will cost.
   Where the existing sites disagree, which result is right is asked as its
   own question, and until you answer every site keeps its present result.
5. **Weigh the corner cases.** A rare input or state whose handling would
   bend the design (a flag through layers, a branch in the general path, new
   state, a new abstraction) comes to you as a corner-case card: who meets
   it, what it costs, and the options cheapest first: reject it at the
   boundary, isolate it at the edge, build it in, or leave it. Until you
   answer, the design stays as it is.
6. **Settle failure behavior:** what the request says a consumer sees on each
   failure, or a question for you. Until it is answered, the error propagates.
7. **Write the placement** into the plan or ticket, or as a change card:
   rules and owners, reuse, reshape steps, corner cases and their decisions,
   what is in and out of scope, failure behavior, and the check to run
   afterwards.

**Check**, after the change:

1. **Pin** the base and head and run the tests at the head.
2. **Take leads on the added lines:** the guards, defaults, handlers, and
   retries the change adds; the classes, modules, and files it adds with
   what each holds, its wrappers, its options nothing sets, and its
   interfaces with one implementation; the added lines no test executes;
   the values it adds in more than one file; and the dependencies it adds,
   with the cycles they close. The skill then reads the diff of every changed file and keeps a
   list of what it read. The leads and the author's description say where to
   look first, not where to stop.
3. **Count decision sites, base against head.** The rules come from the
   diff first, every added or changed condition, constant, and list, and
   then from the description. More sites for a rule is a scattered rule. When several sites hold the same list of kinds or types,
   the skill asks what makes them several: one type added for each value is
   then the finding, and the parallel lists are its evidence. A decision outside the rule's owner is misplaced logic. A
   rule changed at some sites and not at others is behavior to decide, handed
   to `find-bugs` or `fix-bug` with both results.
4. **Account for every added special case,** which includes a parameter or
   flag one caller sets, a mode, and a clamp: its producer and its reason, or
   it is an unjustified special case. The reason comes from the request, the
   ticket, or you; the author's own commit message is an account to follow
   to its source, not the reason. A check where data enters the system is
   fine. An added flag, branch, or state that serves one real case with no
   recorded decision comes to you as a corner-case question, not a finding.
5. **Look at data and state.** For each piece the change adds or writes: one
   place builds or writes it, and a reader can tell what it holds without
   knowing which code ran before. The shapes include a key added to a hash
   another module built, an argument changed in place, a new writer of state
   another module owns, a memo or cache with no rule for when it is stale, a
   new field on a request context, and a kept reference to an object the
   caller still changes.
6. **Look at added dependencies.** Against a stated design, a dependency
   the design does not allow is a needless link. With no stated design, the
   skill reads each added dependency that closes a cycle or is the first of
   one part on another, and asks why the two must change together. A
   dependency that closes a cycle, or a call or write that goes back up to
   the code that called it, is two-way flow: calls and state should move one
   way.
7. **Look for added surplus.** For each module, class, type, or file the
   change adds, the skill names the decision only it makes. One with none,
   because it only delegates, only holds a constant, or only renames another,
   is surplus, confirmed by a deletion test: if deleting it makes complexity
   vanish, it was surplus; if the complexity reappears in every caller, it
   was earning its place. The shapes include a wrapper that only delegates,
   a module or subclass for each value that differs only by a constant, an
   option nothing sets, an interface with one implementation, a compatibility
   path with no outside consumer, and an old path left after its callers
   moved. A new module or class that takes the name of an existing one comes
   to you as a question.
8. **Compare with the placement,** when there is one. A placement settles
   scope, not structure, so the steps above apply to what it proposed too.

The check reports only these kinds, each with its evidence, and "nothing
found" is a result. What it records as checked and fine carries a structure
reason; "behavior is unchanged" clears a behavior question, not a structure
one. Findings that one change would remove are reported as one finding, cause
first: five guards on one missing value are one producer. The limits say how
many changed files were read and name any that were not. When you ask it to apply fixes, a fix deletes, moves,
reuses, or returns a value in place of changing one; it adds no abstraction,
no check, and no test for a state nothing produces.

Prompt shapes:

```text
/aantoniadis-skills:fit-change <the feature or fix you are about to make>
/aantoniadis-skills:fit-change Check <the branch, PR, or working tree> against <base>. <Report only | Apply the fixes that keep behavior.>
```

## The rules it applies

- **One change to a rule touches one place.** When it would touch two, the
  structure is what needs changing, and that is your decision before the
  code is written.
- **Restructuring the placement names is in scope. Everything else stays as
  it is.** This is how a change includes the refactoring it needs without
  growing into a rewrite.
- **A check needs a producer; a fallback needs a decision.** A guard is added
  only with the caller, input, or stored value that produces the state. A
  fallback is added only where the request or you say what the consumer
  should see.
- **Data is built once, and state has one writer.** New code passes a value
  with declared fields and returns a result. It does not add keys to a hash
  another module built, change an argument, or write state another module
  owns.
- **A corner case that bends the design is your call.** The skill shows
  you its reach and its price, and recommends; building it into the general
  design needs your answer. The [corner cases](../skills/CORNER-CASES.md)
  guide holds the card and the defaults.
- **Facts come from the code and from runs; intent comes from you.** The
  skill finds where a rule is decided. It asks you which structure you want
  and what a consumer should see.

## The change card

A run on its own writes a change card, `change-card.md`, and its page, in the
same shape as `untangle`'s map: *In short* with the problem, what we propose,
and what you decide; then one section per problem (why the change does not
fit, each corner case, each finding of a check) with its picture before and
after the change, its evidence side by side, its fix, and its decision; then
the plan for the implementer, with any module it renames, removes,
merges, splits, or moves. Problems are ranked by what the structure costs;
a possible bug comes last, as a behavior to decide. Called from `plan-change` or `fix-bug`, the
placement goes into the slice or the fix instead, with no page.

## Called by other skills

`plan-change` takes a placement for each slice that changes existing code
and writes it into the slice's **Placement** field. `fix-bug` places a fix
before it lands, so a bug whose cause is one rule decided in several places
reaches you as a choice instead of a patch at the symptom.

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

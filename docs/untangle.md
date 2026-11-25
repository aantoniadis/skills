# untangle

Map one component as it is, compare it with the design people believe it has,
and get a rework you choose: for every rule and every piece of state, one
module that owns it. The result is a rework map, `rework-map.md`, with an
HTML page when selected. The skill changes no application code.

Use it on code that has become hard to follow or change, whoever wrote it:
logic for one rule spread across modules and layers, helpers that carry
behavior nobody documented, guards and fallbacks nobody can explain.

## How it works

1. **Scope and baseline.** A kickoff round asks the choices the prompt leaves
   open: the component or flow, the map alone or with a rework proposal, HTML
   or text, and checkpoints or a guided walk through the code together. The
   skill runs the scope's tests once and keeps the result: every later probe
   is compared with it. When the code cannot run, the map says so, claims only
   what the source shows, and proposes no removal.
2. **Stated design.** Before reading internals, it lists what the component
   does for its consumers, in your domain words, and the design your
   documentation, decision records, and layout state. **Checkpoint:** you
   correct both, and say which flows matter and which oddities are deliberate.
3. **Census.** For each capability it lists every place that decides something
   about it, from four kinds of evidence: text search, references, execution,
   and history. Where they disagree is the finding: code a run executes that
   no search for the capability's words found is a hidden part of it; files
   that change together with no dependency between them often hold one rule
   twice. It also lists the scope's special cases: guards, defaults, swallowed
   errors, retries, compatibility paths.
4. **Map and comparison.** Dependencies come from a resolver or from
   `import_edges.py`, and `design_conformance.py` marks each relationship *as
   stated*, *not stated*, or *not found*. The map lists who writes each piece
   of state and draws the main flows as the runs showed them.
   **Checkpoint:** you see the differences first, and say for each whether it
   is intended or drift.
5. **Findings.** Each problem gets one of five names: scattered rule,
   misplaced logic, needless link, surplus, unjustified special case. A
   special case is classified by whether anything reaches it and by what it
   points to: a missing requirement, a producer emitting a state it should
   not, an implicit boundary, or a real outcome. Findings are ranked by what
   they cost at the present rate of change. What looked wrong and is fine is
   recorded, so the next run does not raise it again.
6. **Rework.** Findings are grouped under the change that removes them. The
   map offers two or three targets, one of which leaves the code as it is,
   and recommends one. **Checkpoint:** you choose. The chosen target gets
   ordered steps: pin the behavior with a test seen to fail, subtract, gather
   each rule at its owner, reshape, then lock the design in with a check. A
   behavior change found on the way is a separate decision.
7. **Record and handoff.** The map passes `render_page.py --check`. The skill
   hands over the `plan-change` command with the map path and the chosen
   target, or the step text for one contained step.

Prompt shape:

```text
/aantoniadis-skills:untangle <component, directory, or flow> <what hurts about it, if you know>
```

## What it asks you, and what it does not

It answers from the code, its history, and runs whatever those can answer. It
asks you what only a person knows: why something exists, whether a behavior is
intended, which flows matter, and which design you want. Each answer is
written into the map beside the claim it settles, so a later session reads it
there.

In an unattended run nobody answers. Every question about intent then takes
its conservative default (the behavior is intended, the special case stays,
the stated design stands), marked as a default, and the questions wait for you
in the map's question table. Answer them in a follow-up and the skill updates
the findings, targets, and steps they change.

## What a removal needs

Missing test coverage never justifies removing a guard or a fallback. A
removal is proposed only when the callers are enumerated and none produces
the state, a probe through the public boundary did not reach it, history
gives no reason that still holds, and you agree; or when the check duplicates
one that demonstrably runs earlier on every path. A check at a trust boundary
stays unless an adversarial probe that fails without it has been written.

## The scripts

All four print leads to read, not findings, and write no files.

| Script | Prints |
| --- | --- |
| `change_coupling.py` | The most changed files, and the pairs of files that change in the same commits, marked when no dependency links them. It warns on a shallow clone. |
| `import_edges.py` | Static import edges between tracked files in Python, JavaScript, TypeScript, and Java, as `from<TAB>to`. A floor: use the ecosystem's own resolver when there is one. |
| `design_conformance.py` | Each relationship of a stated design, given as JSON, against those edges: *as stated*, *not stated*, or *not found*. |
| `special_cases.py` | Lines that handle one situation apart from the main path: broad or swallowed error handlers, defaults for missing values, early returns, retries, compatibility paths, suppressed checks. |

## Beside other architecture skills

Matt Pocock's `improve-codebase-architecture` surveys a codebase for modules
worth deepening, from reading and commit history, and interviews you about
the candidate you pick. Use it for a regular survey. Use `untangle` when one
component needs evidence from running code, a comparison with its documented
design, an account of its guards and fallbacks, and ordered steps. A cleanup
command that works on a diff, such as a simplify pass, fits the hour after a
change; `untangle` fits code that has already degraded.

## Limits

- One component or flow per run. For a large scope the map says which
  capabilities were not inspected.
- The map proposes; it does not carry out the rework.
- Edges from static imports miss dependency injection, reflection, and
  lookups by string. The map names its edge source beside each result.
- History counts depend on the fetched history and on how the project
  commits; squash merges and bulk commits distort them.

## Where the method comes from

The steps follow published procedures: reflexion models for comparing a
stated design with extracted dependencies (Murphy, Notkin, and Sullivan),
feature location from textual, static, dynamic, and historical evidence (Dit
and others), change coupling from version history (Tornhill), and
characterization tests seen to fail before a structure moves (Feathers;
Seemann). Several ideas come from other agents' skills: grouping findings
under the one change that removes them, and reading a special case as a
missing requirement (Every's `ce-simplify-code`); pinning behavior and
subtracting before adding (Cursor's pstack refactoring playbook); requiring
an adversarial test before a boundary check goes (oh-my-opencode's
`remove-ai-slops`); the deletion test, and asking the user for decisions and
never for facts (Matt Pocock's `codebase-design` and `grilling`).

# untangle

Map one component as it is, compare it with the design people believe it has,
and get a rework you choose: for every rule and every piece of state, one
module that owns it. The result is a rework map, `rework-map.md`, with an
HTML page when selected. The skill changes no application code; with a rework
proposal it adds the lock tests that protect it, unless you say the project
must not change.

Use it on code that has become hard to follow or change, whoever wrote it:
logic for one rule spread across modules and layers, helpers that carry
behavior nobody documented, guards and fallbacks nobody can explain.

## How it works

1. **Scope and baseline.** A kickoff round asks the choices the prompt leaves
   open: the component or flow, the map alone or with a rework proposal, HTML
   or text, and checkpoints or a guided walk through the code together. The
   skill runs the scope's tests once as they are and once with coverage
   recorded per test: every later probe is compared with that baseline. When
   the code cannot run, the map says so, claims only what the source shows,
   and proposes no removal.
2. **Stated design.** Before reading internals, it lists what the component
   does for its consumers, in your domain words, and the design your
   documentation, decision records, and layout state: the dependencies they
   allow, and the rules they quote, such as "the API layer decides nothing
   about money". **Checkpoint:** you correct these, and say which flows matter
   and which oddities are deliberate.
3. **Census.** For each feature it lists every place that decides something
   about it, from five kinds of evidence: text search, references, execution,
   history, and a deliberate break. Where they disagree is the lead: code a
   run executes that no search for the feature's words found is a hidden
   part of it; files that change together with no dependency between them
   often hold one rule twice; a decision broken on purpose while every test
   stays green is behavior no test protects. It also lists the scope's
   special cases (guards, defaults, errors turned into values, retries,
   compatibility paths) and its shared data: state several modules write,
   and hashes or dicts passed between modules, with the writers and readers
   of each key. It freezes such data where it is handed over and runs the
   tests, to find what changes it afterwards.
4. **Map and comparison.** Dependencies come from a resolver or from
   `import_edges.py`, and `design_conformance.py` marks each one *as stated*,
   *not stated*, or *not found*. Each stated rule is marked *holds*, *broken*,
   or *not checked*. The map lists who writes each piece of state and draws
   the main flows from the source, marking the steps a run executed.
   **Checkpoint:** you see the differences first, and say for each whether it
   is intended or drift.
5. **Problems.** What may be wrong or unwanted in what the component does, a
   possible defect or two sites that disagree, is a problem to decide, ranked
   first, with its run and its handoff. Each structure
   problem gets one of seven names: scattered rule, misplaced logic, needless
   link, surplus, shared mutable state, shapeless data, unjustified special
   case. A special case is classified by
   whether anything reaches it and by what it points to: a missing
   requirement, a producer emitting a state it should not, an implicit
   boundary, or a real outcome. A case that is reached but bends the design
   gets a corner-case card, so you can choose to keep it, isolate it at the
   edge, or reject the case. What looked wrong and is fine is recorded, so
   the next run does not raise it again.
6. **Rework.** Findings are grouped under the change that removes them. The
   map describes one recommended target in full and each alternative in a few
   sentences; one alternative always leaves the structure as it is. When the
   findings do not justify a restructuring, the recommendation is to leave it,
   and the proposal is the tests to write and the check that keeps the stated
   design true. **Checkpoint:** you choose. The chosen target gets ordered
   steps: pin the behavior with a test seen to fail, subtract, gather each
   rule at its owner, reshape, then lock the design in with a check.
7. **Lock the behavior.** With a rework proposal, the skill writes the
   tests that lock what the code does today, unless you say the project
   must not change: every behavior the
   chosen rework moves, and every behavior no test protected. Each is
   written at an interface the rework keeps, seen failing once against a
   deliberate break, and then green on the code as it is. A value under
   decision is recorded as it is today and marked, so your answer changes
   the test on purpose. These tests are the only change the skill makes to
   your project, and it does not commit them unless you allow it.
8. **Record and handoff.** The map's page draws the structure as a picture:
   files grouped by design part, the dependencies the code has, and a dot
   for each place that decides a rule. A switch moves between today and the
   proposal, so you watch each rule's dots travel to their owner and the
   forbidden dependencies disappear. Selecting a rule follows it across
   files, and a table shows which module writes and reads each key of
   shapeless data. The map passes `render_page.py --check`, and every
   pinned line is printed beside its source and read against the map. The
   skill hands over the `plan-change` command with the map path and the
   chosen target, or the step text for one contained step.

Prompt shape:

```text
/aantoniadis-skills:untangle <component, directory, or flow> <what hurts about it, if you know>
```

## The map

The map is written for two readers: a lead who decides whether the rework is
worth it, and the author who carries it out.

- **In short**, at the top: the problem that matters most, what we propose,
  and what you decide. A lead can stop there. Every decision that waits for
  you is gathered under it, linked to its problem.
- **What it does**, written as a spec: each feature in your words, and
  under it each behavior a consumer sees, with what verifies it: *tested*
  (a test fails when it breaks), *locked* (a lock test written for the
  rework), or *untested*. The spec and the tests together are what the
  rework must keep; a behavior marked *untested* gets a lock test before
  any code moves.
- **How the code carries it**: a behavior map, one row per behavior and one
  column per file, marking where it is decided, called, or stored. A row
  decided in more than one file is red and links to the problem that holds
  it, so the weak points are the rows a reader sees first.
- **Problems**, ranked by what the structure costs: scattered rules,
  misplaced logic, needless links, two-way flow (calls or state that go
  back up the layers, or files that depend on each other), surplus,
  shared mutable state, shapeless data, unjustified special cases, and
  unclear names. The
  map is for making code readable; a possible bug it finds on the way is a
  *behavior to decide*, ranked last and handed to `find-bugs` or `fix-bug`.
  Each problem is one section that holds everything
  about it: what is wrong and what it costs, how sure the map is (we ran it,
  read it at the lines, or inferred it), a picture, the evidence, the
  proposed fix with its cost and what you get, the other options with
  *leave it* always among them, and your decision.
- **The pictures** show the problem, not the whole component. A *focus*
  draws only the files and rules of that problem, today and proposed side by
  side. A *change history* draws each past change to a rule against the
  places that decide it, and marks every place a change missed: "4 commits
  changed the rate; 2 of them changed only some of its places". Code
  excerpts sit side by side, so three places that decide one rule are read
  at once.
- **The plan**, for the author: the target, the direction its calls and
  state move in, one way from the entry points down to storage, and the
  module changes: each rename, removal, merge, split, or move, with the
  reason. A module is named for the one decision it owns, one with no
  decision of its own is removed or merged, and one with two reasons to
  change is split. The whole structure has a switch between today and the
  proposal, which shows renamed, removed, and added modules. Then the
  **design principles**: single responsibility, the rest of SOLID, YAGNI,
  minimal shared state, one-way flow, and intention-revealing names, each
  checked on the code today and on the target, so a lead sees what the
  rework buys. The [clean structure](../skills/CLEAN-STRUCTURE.md) guide
  holds the check for each. Then come the lock tests and the steps.
- **What is sound**, and **How it works today** as the reference the
  problems cite, folded on the page until opened.

The page is light, with a dark theme for whoever asks; the sidebar lists the
problems with the state of each decision, and every pinned line opens the
code beside the page.

## After the rework

`plan-change` takes the map's chosen target and your answers as decisions
already made, plans one slice per rework step, and puts the lock tests
first. Once the rework lands, run `untangle` again on the same map. It
reruns the lock tests and the census for the rules the target names, and
reports each target measure before and now, such as decision sites for a
rule going from 3 to 1, as met or not met.

## What it asks you, and what it does not

It answers from the code, its history, and runs whatever those can answer. It
asks you what only a person knows: why something exists, whether a behavior is
intended, which flows matter, and which design you want. Each answer is
written into the map beside the claim it settles, so a later session reads it
there.

In an unattended run nobody answers, so the skill holds no checkpoint and
delivers once. A difference between the code and the stated design is then
marked *open*, neither drift nor intended; every special case stays; the lock
tests of a rework proposal are still written; and the rework steps include
only moves that hold under either answer. The questions
wait for you in the map's question table. Answer them in a follow-up and the
skill updates the findings, targets, and steps they change.

## What a removal needs

Missing test coverage never justifies removing a guard or a fallback. A
removal is proposed only when the callers are enumerated and none produces
the state, a probe through the public boundary did not reach it, history
gives no reason that still holds, and you agree; or when the check duplicates
one that demonstrably runs earlier on every path. A check at a trust boundary
stays unless an adversarial probe that fails without it has been written.

## The scripts

The first seven print leads to read, not findings. Only `break_probe.py`
writes files: its run logs, in the directory you give it.

| Script | Prints |
| --- | --- |
| `change_coupling.py` | The most changed files in scope, and the pairs of files that change in the same commits, including partners outside the scope, marked when no dependency links them. With `--functions`, the same for functions, which finds a rule scattered inside one large file. It warns on a shallow clone. |
| `import_edges.py` | Static import edges between tracked files in Python, JavaScript, TypeScript, and Java, and in Ruby `require_relative` and references to a constant one file defines, as `from<TAB>to`. With `--rev`, at a commit. With `--base`, only the edges a change adds, each with the cycle it closes and the first dependency of one directory on another. With `--cycles`, every group of files that depend on each other, with an example loop, and every pair of directories that do. A floor: use the ecosystem's own resolver when there is one. |
| `design_conformance.py` | Each dependency of a stated design, given as JSON, against those edges: *as stated*, *not stated*, or *not found*. |
| `special_cases.py` | Lines that handle one situation apart from the main path: broad error handlers, errors turned into values, defaults for missing values, early returns, retries, status and version branches, compatibility paths, suppressed checks. |
| `shared_data.py` | Globals, class-level variables, module-level collections, contexts, and memos; and a ledger of hash and dict keys: the files that write each key, the files that read it, and the reads that supply a default. With `--base`, only the state lines a change adds and the keys it uses on an added line. |
| `added_units.py` | What a change adds that may decide nothing, in Python and Ruby: classes, modules, and files with no method or function of their own, grouped when they share a base or a directory and hold only constants; functions that only pass their parameters on; options no caller sets by keyword; units that exactly one unit extends; and units that take the name of another unit. It says what it does not look for, so the absence of a lead clears nothing. `fit-change` runs it on a diff. |
| `added_values.py` | The values a change adds in more than one file: quoted words, symbols, and numbers, with the files that hold each at the head. A lead to one rule kept in several places. |
| `break_probe.py` | Makes each listed break in a scratch worktree, runs the focused tests, reruns a break they miss under the full suite, and reports which behaviors no test protects. |
| `tests_for_line.py` | The tests that execute a source line, from coverage.py data recorded per test. |
| `pinned_lines.py` | The source text behind every pinned line of a note, to read against what the note says. |

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
  features were not inspected.
- The map proposes; it does not carry out the rework.
- Edges from static imports miss dependency injection, reflection, and
  lookups by string. The map names its edge source beside each result.
- `special_cases.py` has no pattern for a clamp, a parameter one caller sets,
  or a retry written without the word. In code whose job is to translate
  errors, most of its leads are the main path.
- The page checker confirms that a pinned line exists and that a claim carries
  an evidence word. It cannot tell whether the line supports the sentence;
  `pinned_lines.py` and a reader do that.
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

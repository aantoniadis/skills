---
name: fit-change
description: Places a change in the existing design before it is written, naming the module that owns each rule it touches and whether the structure must be reshaped first, and checks a finished change for a rule added in a second place, a decision made in the wrong module, and guards, fallbacks, or wrappers nobody asked for. Use when a feature or bug fix is about to be implemented in existing code, when the user asks where a change belongs or whether to refactor first, and when a diff, branch, or PR needs a structure review or a cleanup of slop. Not for deciding behavior (plan-change), finding defects (find-bugs), or a component that has already degraded (untangle).
argument-hint: "<the change to place; or the diff, branch, or PR to check>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Fit change

Keep one change from eroding the design. Before the change, **place** it: say which module owns each rule it touches, what it reuses, and whether the structure has to be reshaped first. After the change, **check** it: find what the diff added in a second place, in the wrong module, or for no stated reason. A rule's **owner** is the one module that decides it. A **decision site** is a place that decides something about a rule: a condition, a default, a validation, a transformation.

Five rules hold for the whole task:

- **One change to a rule touches one decision site.** When it would touch two, the structure is what needs changing, and that is the user's decision to make before the code is written.
- **Restructuring the placement names is in scope. Everything else stays as it is.** This is what lets a change include the refactoring it needs without growing into a rewrite.
- **A check needs a producer; a fallback needs a decision.** A guard is added only with the caller, input, or stored value that produces the state it handles. A fallback or a caught error is added only where the request or the user says what the consumer should see on that failure; otherwise the error propagates.
- **Data is built once, and state has one writer.** New code passes data between modules as a value with declared fields and returns a result; it does not add keys to a hash another module built, change an argument it was given, or write state another module owns.
- **Facts come from the code and from runs; intent comes from the user.** Find where a rule is decided yourself. Ask which structure they want and what a consumer should see.

A request, ticket, or plan with no code yet takes **Place**. A diff, a branch, a PR, or a changed working tree takes **Check**; when a placement exists for it, check against it. A change that touches one site of one rule in familiar code needs three lines of placement and no round.

## Place

1. **Name what the change decides.** List the rules the change adds or alters, in the project's domain words, the state it writes, and the failures it can meet.

2. **Find each rule's decision sites today.** Search the code for the rule's discriminators (enum values, type fields, status strings, flags, configuration keys), follow the references from each hit, and read the history of the lines that hold the rule: `git log -S'<discriminator>' --oneline`. Record every site with its pinned line. Where two sites decide the same rule, run one input through both and record whether they agree. The census reference of [untangle](../untangle/references/census.md) says how each kind of evidence is taken and what it misses. In the same search, look for existing code the change can call before proposing new code.

3. **Test the fit.** The change **fits** when each rule changes at one decision site, in the module that owns it. It does not fit when any of these holds:
   - the same condition, constant, or list has to change in a second file or layer;
   - the change adds one more branch to a chain that already tests the same discriminator, or a flag that has to stay in step with another;
   - a value has to be passed through layers that do not use it, to reach the one place that does;
   - a bug fix would put a check where the symptom appeared, while another place produces the bad state;
   - the change needs one more key in a hash or dict that several modules read and write, or one more writer of state another module owns;
   - the rule's sites already disagree with each other.

4. **Decide.** When the change fits, write the placement. When it does not, put the choice to the user as a checkpoint from [asking](../ASKING.md), recommendation first: **reshape first**, with the behavior-preserving steps that gather the rule at its owner before the change, or **patch**, with the number of sites the rule has afterwards and what the next change to it will cost. Order reshape steps as [rework](../untangle/references/rework.md#order-the-steps) says, each with the test that pins it. Recommend the reshape when it stays inside the rule's own sites; recommend the patch when the reshape would reach code the change has no other reason to touch, and record the reshape as a follow-up. When nobody answers, apply the recommendation and mark it as a default.

   Where the rule's sites disagree, gathering them changes what one of them returns. Which result is right is a behavior decision outside this change: ask it as its own question, and until it is answered keep every site's present result. Gather the sites that agree, leave the one that differs where it is, list it as waiting for the answer, and name its handoff to [fix-bug](../fix-bug/SKILL.md). A likely intent, such as an older copy nobody updated, is your recommendation for the answer; it is not the answer.

5. **Settle failure behavior.** For each failure the change can meet, quote what the request or plan says the consumer sees. Where nothing says, list it as a question; until it is answered the error propagates.

6. **Write the placement** where the implementer reads it: the plan's slice or the ticket when one exists, else `placement.md` at the investigation location that `python3 <package>/skills/investigation_dir.py <topic> <project>` creates and prints. Use these fields:

   ```markdown
   ## Placement

   **Change:** <the request in one sentence>.
   **Rules and owners:** <one line per rule: the rule, its owner with a pinned line, its decision sites today and after the change>.
   **Reuse:** <existing code the change calls, pinned; or none found, with the search>.
   **Data and state:** <the value the change adds or extends, with its fields and the one place that builds it; the one writer of any state it touches; or none>.
   **Reshape first:** <the ordered steps, each structural with its pin; or none: the change fits>.
   **In scope:** <the files and the restructuring named above>. **Out of scope:** everything else.
   **Failure behavior:** <per failure: the quoted decision, or the open question and "the error propagates">.
   **Check after:** <the test command, then fit-change on the diff>.
   ```

Deliver the placement in chat with its pinned lines, the choice made or still open, and the next command. For an implementation the user starts, hand off to `mattpocock:implement` as [package references](../REFERENCES.md) say, with the placement in the command, or give the placement as the scope of a direct implementation.

Done when every rule the change touches has its decision sites listed with pinned lines, the fit is stated with the signal that decided it, the user has chosen or the default is marked, and the placement is where the implementer reads it.

## Check

1. **Pin the change.** Record the head and its base, as [find-bugs](../find-bugs/SKILL.md) does for a PR, a branch, or a working tree. Run the tests once at the head and keep the command and result. Hold the kickoff round from [asking](../ASKING.md) for the one open choice: report only, or also apply the fixes that keep behavior. Recommend applying them when this session wrote the change, and reporting only otherwise.

2. **Take the leads on the added lines.** These print leads; reading the diff finds the rest.

   ```bash
   python3 <package>/skills/untangle/scripts/special_cases.py --base <base> [--head <head>]       # guards, defaults, handlers, retries the change adds
   python3 <package>/skills/find-bugs/scripts/untested_added_lines.py --base <base> --head <head> --repo <checkout> --cov <report>
   ```

   When the project states a design, compare it with the code at the base and at the head, as [census](../untangle/references/census.md#edges-for-the-dependency-view) says, and read every relationship that is *not stated* at the head only.

3. **Count decision sites, base against head.** For each rule the change touches, from the placement or from reading the diff, list its sites before and after.
   - A rule with more sites at the head than at the base is a **scattered rule**.
   - A decision added outside the rule's owner is **misplaced logic**.
   - A rule changed at some of its sites and not at others is **behavior to decide**, not a structure finding: run one input through the changed and the unchanged site, record both results, and hand it to [find-bugs](../find-bugs/SKILL.md) or [fix-bug](../fix-bug/SKILL.md).

4. **Account for every special case the change adds.** For each added guard, default, caught error, retry, or compatibility path, name its producer and its reason as [special cases](../untangle/references/special-cases.md) says. With no producer and no line of the request behind it, it is an **unjustified special case**. A check where data enters the system (user input, an external service, stored data, a file) has its producer by definition and is fine.

5. **Look at the data and state the change touches.** Run `python3 <package>/skills/untangle/scripts/shared_data.py` on the changed files at the head, and read the added lines for these: a key added to a hash or dict that another module built, with the reads of that key that supply a default; an argument changed in place; a new writer of a global, a class-level variable, or a field another module owns. The first is **shapeless data** made worse, the other two are **shared mutable state**. Data a function builds and returns is fine.

6. **Look for surplus the change adds:** a wrapper that only delegates, an option nothing sets, an interface with one implementation, a compatibility path with no consumer outside the repository, and the old path left in place after its callers moved.

7. **Compare with the placement,** when one exists: files and restructuring outside its scope, and steps it named that the change skipped.

Keep the brief this narrow. A reviewer asked to find problems always finds some, and fixing all of them adds abstractions and tests for cases nothing produces. Report only the kinds above, each with its evidence. "Nothing found" is a result: say what was checked.

When applying fixes, a fix deletes, moves, reuses, or returns a value in place of changing one. It adds no abstraction, no check, and no test for a state nothing produces. Rerun the tests after each fix, and leave anything that changes behavior or reaches outside the change as a finding.

Deliver `## Structure findings`, numbered and ranked by how many future changes will pay for each: its name as a consequence, its kind, the pinned line at the head, the evidence (sites at base and head, the missing producer, the writers of a key or a state, the search that found no consumer), and the fix as a suggestion or as applied with the test result. Then `## Behavior to decide` with its runs and handoffs, `## Checked and fine` for what a reader would flag and the reason it stands, and the limits. Save the delivery as `structure.md` at the investigation location that `python3 <package>/skills/investigation_dir.py <topic> <project>` creates and prints, with the base and head in its first line. That location is ignored by Git and is no part of the change, so a report-only check writes there too.

When the same kind of finding appears in a second change to the project, propose the matching line for the project's instructions, or a check the project runs, from [house rules](references/house-rules.md). Write it only within authorization, as [asking](../ASKING.md) says.

Done when every rule the change touches has its sites counted at base and head, every added special case has a producer or is a finding, the tests' result at the head is recorded, and the delivery says what was checked and what was not.

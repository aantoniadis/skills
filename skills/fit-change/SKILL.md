---
name: fit-change
description: Places a change in the existing design before it is written, naming the module that owns each rule it touches and whether the structure must be reshaped first, and checks a finished change for a rule added in a second place, a decision made in the wrong module, and guards, fallbacks, or wrappers nobody asked for. Use when a feature or bug fix is about to be implemented in existing code, when the user asks where a change belongs or whether to refactor first, and when a diff, branch, or PR needs a structure review or a cleanup of slop. Not for deciding behavior (plan-change), finding defects (find-bugs), or a component that has already degraded (untangle).
argument-hint: "<the change to place; or the diff, branch, or PR to check>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Fit change

Keep one change from eroding the design. Before the change, **place** it: say which module owns each rule it touches, what it reuses, and whether the structure has to be reshaped first. After the change, **check** it: find what the diff added in a second place, in the wrong module, or for no stated reason. A rule's **owner** is the one module that decides it. A **decision site** is a place that decides something about a rule: a condition, a default, a validation, a transformation. A **unit** is a module, class, type, or file.

Seven rules hold for the whole task:

- **One change to a rule touches one decision site.** When it would touch two, the structure is what needs changing, and that is the user's decision to make before the code is written.
- **Restructuring the placement names is in scope. Everything else stays as it is.** This is what lets a change include the refactoring it needs without growing into a rewrite.
- **A check needs a producer; a fallback needs a decision.** A guard is added only with the caller, input, or stored value that produces the state it handles. A fallback or a caught error is added only where the request or the user says what the consumer should see on that failure; otherwise the error propagates. An error the change raises names what failed with the values that identify it, and keeps its cause.
- **Data is built once, and state has one writer.** New code passes data between modules as a value with declared fields and returns a result; it does not add keys to a hash another module built, change an argument it was given, or write state another module owns.
- **New code meets [clean structure](../CLEAN-STRUCTURE.md).** Each unit the change adds or reshapes has one responsibility and a name that says what it is for; it adds no abstraction without a second user today, and no state another module writes.
- **A corner case that bends the design is the developer's call.** Handling a rare input or state with a flag through layers, a branch in the general path, new state, or a new abstraction waits for their choice on a corner-case card, as [corner cases](../CORNER-CASES.md) says.
- **Facts come from the code and from runs; intent comes from the user.** Find where a rule is decided yourself. Ask which structure they want and what a consumer should see.

When [plan-change](../plan-change/SKILL.md) or [fix-bug](../fix-bug/SKILL.md) calls the place step as a helper, hold no round of your own: return the placement for the caller's slice or fix, and pass any reshape-or-patch choice and every corner-case card back to the caller, which puts them to the user. A request, ticket, or plan with no code yet takes **Place**. A diff, a branch, a PR, or a changed working tree takes **Check**; when a placement exists for it, check against it. A change already checked at an earlier head takes **Re-check**. A change that touches one site of one rule in familiar code needs three lines of placement and no round.

## Place

1. **Name what the change decides.** List the rules the change adds or alters, in the project's domain words, the state it writes, the failures it can meet, the corner cases it meets, and the units it adds, each with the decision only it makes. A unit that would make none stays out of the placement: values that differ only by a constant go in one list or table, and a call goes straight to the code a wrapper would hide.

2. **Find each rule's decision sites today.** Search the code for the rule's discriminators (enum values, type fields, status strings, flags, configuration keys), follow the references from each hit, and read the history of the lines that hold the rule: `git log -S'<discriminator>' --oneline`. Record every site with its pinned line. Where two sites decide the same rule, run one input through both and record whether they agree. The census reference of [untangle](../untangle/references/census.md) says how each kind of evidence is taken and what it misses. In the same search, look for existing code the change can call before proposing new code.

3. **Test the fit.** The change **fits** when each rule changes at one decision site, in the module that owns it. It does not fit when any of these holds:
   - the same condition, constant, or list has to change in a second file or layer;
   - the change adds one more branch to a chain that already tests the same discriminator, or a flag that has to stay in step with another;
   - a value has to be passed through layers that do not use it, to reach the one place that does;
   - a bug fix would put a check where the symptom appeared, while another place produces the bad state;
   - the change needs one more key in a hash or dict that several modules read and write, or one more writer of state another module owns;
   - the rule's sites already disagree with each other.

4. **Decide.** When the change fits, write the placement. When it does not, put the choice to the user as a checkpoint from [asking](../ASKING.md), recommendation first: **reshape first**, with the behavior-preserving steps that gather the rule at its owner before the change, or **patch**, with the number of sites the rule has afterwards and what the next change to it will cost. Order reshape steps as [rework](../untangle/references/rework.md#order-the-steps) says, each with the test that pins it; the first step writes the lock tests for the behavior the reshape moves, as [lock tests](../untangle/references/lock-tests.md) says. Recommend the reshape when it stays inside the rule's own sites; recommend the patch when the reshape would reach code the change has no other reason to touch, and record the reshape as a follow-up. When nobody answers, apply the recommendation and mark it as a default.

   Where the rule's sites disagree, gathering them changes what one of them returns. Which result is right is a behavior decision outside this change: ask it as its own question, and until it is answered keep every site's present result. Gather the sites that agree, leave the one that differs where it is, list it as waiting for the answer, and name its handoff to [fix-bug](../fix-bug/SKILL.md). A likely intent, such as an older copy nobody updated, is your recommendation for the answer; it is not the answer.

5. **Weigh the corner cases.** For each corner case the change meets, from the request, the runs, and step 1, decide whether handling it bends the design, as [corner cases](../CORNER-CASES.md) lists. A case handled by a check at one site is placed with the change. For a case that bends the design, write its corner-case card with the options cheapest first and put it to the user in the same round as the reshape choice. When nobody answers, apply the default that guide gives and mark it.

6. **Settle failure behavior.** For each failure the change can meet, quote what the request or plan says the consumer sees. Where nothing says, list it as a question; until it is answered the error propagates.

7. **Write the placement** where the implementer reads it. For a plan's slice or a ticket, write it there with the fields below. Otherwise write the **change card**: fill [card-template.md](references/card-template.md) as `change-card.md` at the investigation location that `python3 <package>/skills/investigation_dir.py <topic> <project>` creates and prints, removing unused prompts. When the script says the location already holds notes, read them before you write: update a card of the same change in place, and start from the template only when the location holds no card. Its problems follow [map format](../untangle/references/map-format.md#problems): why the change does not fit, and each corner case that bends the design, each with its picture, evidence, options, and decision. Its structure view, a `structure-view` fence as [map format](../untangle/references/map-format.md#pictures) describes, shows the files the change touches before (`today`) and after the change (`proposed`), with `"labels": {"today": "Before", "proposed": "After the change"}`. A card with problems lists the design principles as the eleven items under `### Design principles` that the template shows, and the page draws them as a scorecard; a placement that fits leaves the section out. Render and check the card with `python3 <package>/skills/render_page.py <change-card.md> --sync-labels`. The fields for a slice or ticket:

   ```markdown
   ## Placement

   **Change:** <the request in one sentence>.
   **Rules and owners:** <one line per rule: the rule, its owner with a pinned line, its decision sites today and after the change>.
   **Reuse:** <existing code the change calls, pinned; or none found, with the search>.
   **New units:** <each module, class, type, or file the change adds, with the decision only it makes; or none>.
   **Data and state:** <the value the change adds or extends, with its fields and the one place that builds it; the one writer of any state it touches; or none>.
   **Reshape first:** <the ordered steps, each structural with its pin; or none: the change fits>.
   **Corner cases:** <per case that bends the design: the chosen option and its authority, or the open card and its default; or none met>.
   **In scope:** <the files and the restructuring named above>. **Out of scope:** everything else.
   **Failure behavior:** <per failure: the quoted decision, or the open question and "the error propagates">.
   **Check after:** <the test command, then fit-change on the diff>.
   ```

Deliver the placement in chat with its pinned lines, the reshape-or-patch choice with both options (the one applied or recommended, and what the other would cost in sites and at the next change), one line for each corner case that bends the design (the case, who meets it, what handling it would add, and the option applied or chosen), and the next command. For an implementation the user starts, hand off to `mattpocock:implement` as [package references](../REFERENCES.md) say, with the placement in the command, or give the placement as the scope of a direct implementation.

Done when every rule the change touches has its decision sites listed with pinned lines, the fit is stated with the signal that decided it, every corner case that bends the design has a card, the user has chosen or each default is marked, and the placement is where the implementer reads it.

## Check

1. **Pin the change and open its record.**
   - Record the head and its base, as [find-bugs](../find-bugs/SKILL.md) does for a PR, a branch, or a working tree.
   - Create the investigation location with `python3 <package>/skills/investigation_dir.py <topic> <project>`. When the script says the location already holds notes, read them before you write there. A `change-card.md` for the same base and head is updated in place, and so is the card of this change's placement; a card for an earlier head takes **Re-check**. Start from [card-template.md](references/card-template.md) only when the location holds no card. The location is no part of the change, so a report-only check writes there too.
   - Hold the kickoff round from [asking](../ASKING.md) for the one open choice: report only, or also apply the fixes that keep behavior. Recommend applying them when this session wrote the change, and reporting only otherwise. A card already at the location has settled the choice.
   - Run the tests once at the head and keep the command and result under `runs/` at that location. Write each probe there too, and cite both from the card by relative path. A probe is a file outside the checkout that loads the project's test helper, so the checkout you inspect stays as pinned.
   - When the tests fail at the head, say so first in *In short* and on the card's **Blocks merging:** line: the count, the test names, and whether the change's own commits caused the failures. Hand them to [find-bugs](../find-bugs/SKILL.md) or [fix-bug](../fix-bug/SKILL.md), and go on with the structure check.

2. **Take the leads on the added lines.** These print leads; reading the diff finds the rest.

   ```bash
   python3 <package>/skills/untangle/scripts/special_cases.py --base <base> [--head <head>]       # guards, defaults, handlers, retries the change adds
   python3 <package>/skills/untangle/scripts/added_units.py --base <base> [--head <head>]         # units, wrappers, options, and single implementations the change adds (Python, Ruby)
   python3 <package>/skills/untangle/scripts/added_values.py --base <base> [--head <head>]        # values the change adds in more than one file
   python3 <package>/skills/untangle/scripts/import_edges.py --base <base> [--head <head>]        # dependencies the change adds, with the cycles they close
   python3 <package>/skills/find-bugs/scripts/untested_added_lines.py --base <base> --head <head> --repo <checkout> --cov <report>
   ```

   Read the diff of every changed file. The leads and the change's own description say where to look first; neither says where to stop. Keep a list of the changed files, each *read* or *not inspected* with the reason. When the diff is too large for one session, give groups of files, split by rule or by directory, to [investigators](../INVESTIGATE.md) through [native delegation](../WORKERS.md) with these steps. The untested added lines serve steps 4 and 7: an added special case that no test executes has no test as its producer, and an added unit that no test executes is a lead to surplus. List each added decision no test executes in the limits. Before you say that no coverage report was available, look for the project's coverage switch in its test helper and CI configuration and run the changed tests with it. A test file that pins behavior a problem names is read in full before the problem is written.

   Look for a stated design first: the project's architecture and domain documents, and any document the change itself edits. Record where you looked. Take the parts and the stated rules from what you find, even when it states no allowed dependencies; when you find none, say so with the search, and draw the view as [map format](../untangle/references/map-format.md#pictures) says for no stated design. When the project states a design, compare it with the code at the base and at the head, as [census](../untangle/references/census.md#edges-for-the-dependency-view) says, and read every relationship that is *not stated* at the head only.

3. **Count decision sites, base against head.** For each rule the change touches, list its sites before and after. Take the rules from the diff first: every added or changed condition, constant, and list names a rule, and so does each value step 2 printed as added in more than one file. Then add the rules the placement and the change's description name. The description says what its author looked at; the diff says what changed.
   - A rule with more sites at the head than at the base is a **scattered rule**. When several sites hold the same list or registry, such as kinds, types, or handlers, ask what makes them several. If the change added one unit for each value, report that as the finding, as step 7 says, and the parallel lists as its evidence.
   - A decision added outside the rule's owner is **misplaced logic**.
   - A call or a write the change adds from a later part back to an earlier one, or a cycle it closes, is **two-way flow**: calls and state should move one way.
   - A unit the change adds or changes whose name says less than its body does, describes the mechanism, or is generic, such as *manager*, *helper*, or *utils*, is an **unclear name**: propose the name for what it does. A function whose body is complex keeps a name for what it does and gets a one-line comment of why it exists.
   - A function the change adds or grows that a reader cannot follow top to bottom is a **hard-to-follow function**: read it for the signs [clean structure](../CLEAN-STRUCTURE.md) lists under readable functions, such as nesting that guard clauses would flatten, a compound condition with no name, or a boolean argument that selects the behavior.
   - A rule changed at some of its sites and not at others is **behavior to decide**, not a structure finding: run one input through the changed and the unchanged site, record both results, and hand it to [find-bugs](../find-bugs/SKILL.md) or [fix-bug](../fix-bug/SKILL.md).

4. **Account for every special case the change adds.** A **special case** is code that exists for one situation: a guard, a default, a caught error, a retry, a compatibility path, and what the script has no pattern for, such as a parameter or flag one caller sets, a mode, or a clamp. For each one, name its producer and its reason as [special cases](../untangle/references/special-cases.md) says. The reason is a line of the request, the ticket, or the user's answer. The change's own description and commit message are its author's account: follow a reference in them to the request, and when the request cannot be read, record the reason as *stated by the author*. With no producer and no reason, the case is an **unjustified special case**. With no producer and a reason only the author's account gives, it is a question for the user. A check where data enters the system (user input, an external service, stored data, a file) has its producer by definition and is fine. An added case with a producer whose handling bends the design, as [corner cases](../CORNER-CASES.md) lists, and has no recorded decision is a question, not a finding: write it as a problem of the kind corner case, with its options and its decision.

5. **Look at the data and state the change touches.** For each piece of data or state the change adds or writes, name the one place that builds or writes it, and ask whether a reader can tell what the value holds without knowing which code ran before. Run `python3 <package>/skills/untangle/scripts/shared_data.py --base <base> [--head <head>]`, and read the added lines. A key added to a hash or dict that another module built, with the reads of that key that supply a default, is **shapeless data** made worse. These are **shared mutable state**: an argument changed in place; a new writer of a global, a class-level variable, or a field another module owns; a value computed once and kept, such as a memo, a cache, or a lazily set field, with no rule for when it is stale; a new field on a request or thread context; a reference kept to a mutable object the caller still holds; and a stored field the change writes from a second module. Data a function builds and returns is fine.

6. **Look at the dependencies the change adds.** Take them from the edges step 2 printed, or from the ecosystem's resolver at the base and at the head. Where the project states a design, a relationship that is *not stated* at the head only is a **needless link**. Where it states none, read each added edge that carries a note: a cycle the change closes; the first dependency of one part on another, above all when the other already depends on it; and a dependency of code many files use on code that serves one feature. For each, name the reason the two must change together. A cycle the change closes, or an edge from a later part back to an earlier one, is **two-way flow**; another edge with no reason is a needless link, and the usual fix passes the value in or moves the decision to the side that already depends on the other.

7. **Look for surplus the change adds.** Take the leads step 2 printed, and read the diff for what the script says it does not look for. For each unit the change adds, name the decision only it makes. A unit with none, because it only delegates, only holds a constant, or only renames another unit, is **surplus**. Confirm it by the deletion test: if deleting the unit makes complexity vanish, it was surplus; if the complexity reappears in every caller, it was earning its place. The shapes to look for: a wrapper that only delegates; a module or subclass for each value of a discriminator, whose members differ only by a constant, where the values belong in one list or table; an option nothing sets; an interface with one implementation; a compatibility path with no consumer outside the repository; and the old path left in place after its callers moved. An added unit that takes the name of another unit is a question for the user, to keep the name or change it: inside its namespace the name now means the new unit. A unit the base already holds, with callers at the base, is outside this step. When the change left such a unit with no decision of its own, say so, and keep its removal apart from the finding as a follow-up the user decides, because its callers and tests are outside the change.

8. **Compare with the placement,** when one exists: files and restructuring outside its scope, and steps it named that the change skipped. A placement settles scope, not structure: steps 3 to 7 apply to what it proposed as much as to what it left out.

Keep the brief this narrow. A reviewer asked to find problems always finds some, and fixing all of them adds abstractions and tests for cases nothing produces. Report only the kinds above, each with its evidence. "Nothing found" is a result: say what was checked.

Findings that one change would remove are one finding. Name the cause, list the others as its evidence, and rank it by everything it explains: five guards on one missing value are one producer, and three lists of kinds are one type for each value.

When applying fixes, a fix deletes, moves, reuses, or returns a value in place of changing one. It adds no abstraction, no check, and no test for a state nothing produces. Rerun the tests after each fix, and leave anything that changes behavior or reaches outside the change as a finding.

Hold every proposed fix and every option of the card to the same test as the change: run the fit test of Place step 3 on it before delivery. An option that adds a site for a rule another problem of the card gathers says so, and names that problem's owner as the place for it.

Deliver the findings in the change card, as [the card template](references/card-template.md) and [map format](../untangle/references/map-format.md#problems) say:

- **Problems**, numbered and ranked by how many future changes will pay for each, with possible bugs (behavior to decide) last. Each has its name as a consequence, its kind, how sure, what is wrong with the pinned lines at the head, its evidence, and the fix as a suggestion or as applied with the test result. The evidence is the sites at base and head, the missing producer, the writers of a key or a state, or the search that found no consumer, as excerpts side by side where the code makes the point. A fix that moves a decision or changes an interface carries a **Proposed code:** sketch. At most five problems are written in full and the rest in brief. A rule changed at some sites and not at others is a problem of the kind behavior to decide, with its runs and handoff.
- **Decisions.** Each open decision says whether it blocks a step or can wait. In a report-only check every decision is *open*, with its recommended default named; *default applied* is for a change this session made.
- ***In short*** holds the most consequential finding and its fix, and **Inspected source** the base and head.
- ***The plan*** holds a structure view of the head (`today`) against the head with the proposed fixes (`proposed`), labelled `"labels": {"today": "At the head", "proposed": "With the proposed fixes"}`, of the files the findings name, with a `structure-focus` under each problem it pictures. What the change did to each rule, base against head, goes in the problem's evidence as a count of sites. A card with problems lists the design principles as the template's eleven items, head against the proposed fixes; the page draws them as a scorecard.
- ***What is sound*** holds what a reader would flag and the reason it stands. The reason is about structure: the unit makes a decision of its own, or deleting it would push complexity into its callers. "Behavior is unchanged" and "the code moved as it was" are behavior results: they answer what the change's author asked to have verified, and leave the structure question open.
- ***Limits*** holds the count of changed files read, each file not inspected, and the **Leads:** field: each lead the scripts printed, with its producer, its decision, or the problem that holds it.

Render and check the card with `python3 <package>/skills/render_page.py <change-card.md> --sync-labels`. Before any part of the card leaves the machine, as a comment, a post, or a published page, a [second reader](../FRESH-REVIEW.md) compares each claim that leaves with its line or run.

When the same kind of finding appears in a second change to the project, counted as a finding of this check plus a pinned earlier commit or an earlier card that shows the same kind, propose the matching line for the project's instructions, or a check the project runs. Read [house rules](references/house-rules.md) before you word it, and write the proposal under `### House rule` in *The plan*: the line, where it applies, why, and the two occurrences. Write it into the project only within authorization, as [asking](../ASKING.md) says.

Done when every rule the change touches has its sites counted at base and head, every added special case has a producer or is a finding, every added dependency with a note has its reason or is a finding, every added unit has the decision it makes or is a finding, every changed file is read or listed as not inspected, the tests' result at the head is recorded, and the delivery says what was checked and what was not.

## Re-check

When the investigation location holds a card for an earlier head of the same change, resume it. The kickoff choice of the earlier check holds.

1. List the commits that arrived since the card's head and the files they touch. Compare each commit's date with the card's: a commit written before the card did not answer it, so say only that the two agree.
2. Copy the earlier card to `change-card.<short head>.md`, and update `change-card.md` in place. When the earlier page is wanted, render the copy: a copied page links the new card.
3. Run Check again, base against the new head: the tests, every lead script of step 2 and `shared_data.py`, and steps 3 to 8. Read the diff between the two heads in full, and the stated design again when the change edits it.
4. Give each earlier problem a **Resolution:** from the shared label key, with the commit that changed it: *Resolved*, with the pinned line at the new head that shows it; *Open*, with what remains and the current problem that holds it; or *Accepted tradeoff*, with the author's decision quoted and linked. Label a problem that a fix created as introduced by that fix, as [evidence](../EVIDENCE.md#identify-the-evidence) says.
5. Account again for every special case, option, and unit the leads print: a lead the earlier card accounted for and the new card does not mention is a gap.
6. Write the resolutions under `## Since the previous check`, after *In short*, then the current problems as Check says.

Done when every earlier problem has its resolution and commit, the tests and leads ran at the new head, and the earlier card is kept beside the new one.

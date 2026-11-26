# Rework map format

Read when filling or updating a rework map, or the change card of
[fit-change](../../fit-change/SKILL.md), which has the same shape. The map is
one note, `rework-map.md`, written for two readers who were not there: a lead
who decides whether the rework is worth it, and the author who carries it
out. Its purpose is code that reads and changes easily: it states what the
component does, shows how the code carries each behavior and where that is
weak, and proposes the restructuring. Possible bugs are a side result. Follow the [shared page workflow](../../HTML-PAGES.md) for rendering,
and [evidence](../../EVIDENCE.md) for every claim and diagram.

## Contents

- [Order and growth](#order-and-growth)
- [In short](#in-short)
- [What it does](#what-it-does)
- [How the code carries it](#how-the-code-carries-it)
- [Problems](#problems)
- [A worked problem](#a-worked-problem)
- [Pins](#pins)
- [Pictures](#pictures)
- [The plan and the reference](#the-plan-and-the-reference)
- [Names](#names)
- [Diagrams](#diagrams)

## Order and growth

Keep the template's order: *In short*; *What it does*, the behavior as a spec;
*How the code carries it*, each behavior mapped to the code; the problems;
the plan; what is sound; and *How it works today* as reference. The spec and
the map come before the problems because each problem is a weak point of
that map. The map grows through the task: after step 2 it holds *In short*
as far as it is known, the spec, and the stated design; steps 3 and 4 add
the behavior map and the reference; steps 5 and 6 write the problems and the
plan. Remove a section that has nothing to hold, and say in
*Limits* what was left out. A map delivered at a checkpoint passes the check
as it stands.

## In short

Three labelled paragraphs, a few sentences each, that a lead reads and stops:

- **The problem:** the most consequential problem in the reader's terms,
  what it costs, and its evidence. When there are several, the one that
  matters most and the count of the others.
- **What we propose:** the recommended target, what changes, and what
  protects the change, or that the structure should stay as it is and why.
- **What you decide:** each decision that waits for the user in one line,
  with its default; or that none waits.

Then the scope, the inspected source, and what ran. When the scope could not
run, the *What ran* line says so first.

## What it does

The component's behavior, written as a spec: what a consumer can rely on, in
the project's domain words, grouped under one `###` heading per feature in
the user's order of importance. Each behavior is one list item:

```markdown
- **A gold customer gets 10% off at checkout.** When a gold customer checks out, the total is the subtotal less 10%, from [views.py:31](...). *Verified by:* tested, `test_gold_checkout_total` ([test_shop.py:12](...)).
```

- Write each behavior as a condition and its result, as a consumer sees it,
  with its entry point pinned. State what the code does today, not what it
  should do; a result that may be wrong is still stated, and the problem
  that questions it names it.
- **Verified by:** starts with *tested* (an existing test fails when the
  behavior changes, seen under a deliberate break or asserted at a pinned
  line), *locked* (a lock test of this rework records it), or *untested*,
  then the test names or the reason no test protects it.

This spec and the tests it names are what the rework is verified against: a
step is done when every behavior still holds and every test that verifies
one still passes. A behavior marked *untested* is unprotected until a lock
test records it. A feature the code performs and no document or person
named is marked *not stated anywhere* in its first behavior.

## How the code carries it

One sentence with the takeaway, then a `behavior-map` fence: one row per
behavior of the spec, one column per file that takes part, each cell what
that file does for it, and the row's weak point linked to its problem. A
behavior decided in more than one file stands out on the page.

```json
{"files": [{"id": "views", "path": "shop/api/views.py"},
           {"id": "discounts", "path": "shop/pricing/discounts.py"},
           {"id": "serializers", "path": "shop/api/serializers.py"}],
 "behaviors": [{"feature": "Loyalty discount", "name": "A gold customer gets 10% off at checkout",
                "sites": [{"file": "views", "at": "shop/api/views.py:31", "role": "calls"},
                          {"file": "discounts", "at": "shop/pricing/discounts.py:12", "role": "decides"},
                          {"file": "serializers", "at": "shop/api/serializers.py:44", "role": "decides"}],
                "weak": "the rate is decided twice", "problem": 1}]}
```

`role` is *decides* (the file makes a decision of the behavior), *calls*
(the behavior passes through it), or *stores* (it writes the behavior's
state). `weak` names the weak point in a few words, and `problem` is the
number of the problem that holds it; a behavior with none leaves both out.
Keep the columns to the files the behaviors touch, in the order of the
design's parts, so a row that jumps back and forth shows calls that do not
move one way.

## Problems

A **problem** is one thing that makes the component costly to change or
possibly wrong, with what to do about it. It is the unit of the map: each
problem holds its own evidence, picture, fix, and decision, so a reader
never assembles one from several sections. Rank them by what they cost
the people who change the code: structure problems and corner cases first,
by how many places one change must touch times how often the rule changes;
problems of the kind *behavior to decide*, possible bugs, last, because this
map is for restructuring and each of them goes to fix-bug or plan-change. The checker rejects any other kind placed after the first behavior to decide. Number them in their
headings, `### 1. <title>`, and refer to them as *problem 1*.

The title states the consequence a lead understands, such as *Changing a
loyalty rate takes three edits*, not the mechanism, such as *Discount logic in
serializer*. A behavior to decide whose recommended answer keeps today's
behavior is titled as its question, such as *Should a failed rebuild keep
serving its old data?*

Each problem has these labelled paragraphs, in this order. The label starts
the paragraph in bold; the checker reads the first four.

- **Kind:** one of *scattered rule*, *misplaced logic*, *needless link*,
  *two-way flow*, *surplus*, *shared mutable state*, *shapeless data*,
  *unjustified special case*, *unclear name*, *hard-to-follow function*, *corner case*, or *behavior to decide*; then **How sure:**, one of
  *observed* (a run showed it), *source* (read at the lines), or *inferred*,
  with what ran or was read; then **Cost today:**, what it costs each change
  or each user, with its evidence. The three share one line, joined by ` · `.
- **What is wrong:** what happens and why it hurts, in as many paragraphs as
  it needs, with pinned lines and runs. Write for the lead first: what a user
  of the software or a person changing the code meets.
- The picture, when one shows the problem better than words: a
  `structure-focus` fence, a `change-history` fence, or both. See
  [pictures](#pictures).
- **Evidence:** the decisive excerpts as fences with `url="..."`, one after
  another so the page sets them side by side, then a list of the runs,
  searches, and history that support the problem. Show the lines that make
  the point: the three places that decide a rate, not the files around them.
- **Proposed fix:** what changes to remove the problem, labelled *proposed*,
  and where the steps are. For behavior to decide, the handoff to fix-bug or
  plan-change and the question that decides it.
- **Cost and risk:** the files, call sites, and lock tests the fix needs, and
  what can go wrong.
- **What you get:** the measure, before and after, such as the decision
  sites for the rule going from 3 to 1.
- **Other options:** a list, each option in bold with what it changes and
  costs. *Leave it* is always one of them, with what the problem keeps
  costing at its present rate. A corner case lists its options cheapest
  first, as [corner cases](../../CORNER-CASES.md) says.
- **Decision:** one of *open*, *default applied*, *decided*, or *none
  needed*, then the recommendation and what holds until the user answers, or
  the answer with its date. The page gathers every open decision under *In
  short*, so each one stands on its own.

A behavior to decide and a corner case need no **Proposed fix:**, **Cost and
risk:**, or **What you get:** when the decision is all there is; every other
kind has a **Proposed fix:**, even if the fix is to leave it, with the
reason.

## A worked problem

One complete problem, as it stands in a map; a change card writes its
problems the same way. The shop, files, and commits are invented. `<sha>`
stands for the inspected revision, and the structure view this focus names
sits in *The plan*.

````markdown
### 2. Changing a loyalty rate takes three edits

**Kind:** scattered rule · **How sure:** source, read at the lines, and history · **Cost today:** 3 files per rate change; 2 of the last 4 changes missed one

**What is wrong:** The discount for each tier is decided in `pricing`, again in the API serializer for display, and again in quotes. Nothing ties the three together, so a person changing a rate must know all of them. Two of the four changes in the history missed one; that is how gold quotes came to differ from checkout (source, at the pinned lines; history from `git log -L`).

```structure-focus
{"rules": ["Loyalty discount rate"]}
```

```change-history
{"rule": "Loyalty discount rate",
 "sites": [{"id": "discounts", "label": "pricing/discounts.py:12"},
           {"id": "serializers", "label": "api/serializers.py:44"},
           {"id": "builder", "label": "quotes/builder.py:27", "since": "3be62b3"}],
 "commits": [{"sha": "3be62b3", "date": "2023-02-17", "subject": "Quotes compute the discount locally", "changed": ["builder"]},
             {"sha": "93548a8", "date": "2023-09-01", "subject": "Raise gold to 10%", "changed": ["discounts", "serializers"]}]}
```

**Evidence:**

```python url="https://github.com/acme/shop/blob/<sha>/shop/pricing/discounts.py#L12-L13"
RATES = {"gold": Decimal("0.10"), "silver": Decimal("0.05")}
return subtotal * RATES.get(tier, Decimal("0"))
```

```python url="https://github.com/acme/shop/blob/<sha>/shop/quotes/builder.py#L26-L28"
def discount_for(customer, subtotal):
    if customer.tier == "gold":
        return subtotal * Decimal("0.05")
```

- `discounts.py` and `builder.py` changed together in 6 commits with no dependency between them (`change_coupling.py --edges`).

**Proposed fix:** *Pricing owns discounts*: `loyalty_discount(tier, subtotal)` at [discounts.py:12](https://github.com/acme/shop/blob/<sha>/shop/pricing/discounts.py#L12) is the only place that knows a rate; the serializer and the quote builder call it. The steps are in [the plan](#the-plan).

**Cost and risk:** 3 files and 2 call sites change; 2 lock tests come first (proposed).

**What you get:** the next rate change is one edit in one file; decision sites for the rule go from 3 to 1 (proposed).

**Other options:**

- **Leave it:** every rate change keeps touching three files, and the next missed file is found by a customer (inferred from the history).
- **A shared rate table the three places read:** removes the disagreement, but three places still apply the rate (proposed).

**Decision:** open. Recommended: *Pricing owns discounts*. Until you answer, the structure stays as it is.
````

What each part does on the page:

- The `### 2.` heading becomes the problem's number and title, and the
  sidebar lists it with the state of its decision.
- The **Kind:** line becomes the problem's tags; its three labels stay on one
  line, joined by ` · `.
- The `structure-focus` fence draws the files of that rule, today and
  proposed side by side. The `change-history` fence draws each commit against
  the places it changed, and marks the place a commit missed:
  `93548a8` changed two places and missed `quotes/builder.py:27`.
- The two excerpt fences sit side by side because nothing stands between
  them. Each `url` is the same pinned link the text would use: the path at
  the inspected revision and the lines shown, as `#L26-L28`. The lines in the
  fence are the lines at that link.
- The **Decision:** box is coloured by its first word, and an *open* or
  *default applied* decision is also listed under *In short*.

## Pins

Pin committed code at its commit. For a repository with a hosted remote,
build the link from `git remote get-url origin` and the inspected revision:
`[discounts.py:12](https://<host>/<owner>/<repo>/blob/<sha>/shop/pricing/discounts.py#L12)`.
With no hosted remote, link the path relative to the map with the same
anchor, and state the revision in *In short*. Take line numbers from the file
at that revision. An excerpt fence carries the same link as its `url`.

## Pictures

**The structure view.** *The plan* holds one `structure-view` fence of JSON:
the files that the problems name, grouped by design part, the dependencies
between them, a lettered dot for each place that decides a rule, and for
shapeless data the keys and who writes and reads them. The page draws it
with a switch between today and the proposal. The sentence before the fence
states the takeaway and the evidence kind, as
[evidence](../../EVIDENCE.md#diagrams) says for a diagram.

```json
{"parts": [{"id": "api", "label": "API", "said": "only translates requests"},
           {"id": "pricing", "label": "Pricing", "said": "every price is decided here"}],
 "outside": {"today": "Not named in the design", "proposed": "Now named in the design"},
 "files": [{"id": "views", "path": "shop/api/views.py", "part": "api"},
           {"id": "discounts", "path": "shop/pricing/discounts.py", "part": "pricing"},
           {"id": "basket", "path": "shop/basket.py", "part": "outside"}],
 "dependencies": [{"from": "views", "to": "discounts", "today": "as stated", "proposed": "as stated",
                   "at": "shop/api/views.py:4", "why": "The design allows it."}],
 "rules": [{"name": "Loyalty discount rate", "owner": "discounts", "outcome": "moves", "note": "...",
            "sites": [{"file": "discounts", "at": "shop/pricing/discounts.py:12", "what": "gold 10%"},
                      {"file": "views", "at": "shop/api/views.py:40", "what": "gold 5%", "waits": true}]}],
 "data": [{"name": "The order dict", "proposed": "an Order value built once in views.py",
           "keys": [{"key": "total", "writes": [{"file": "views", "at": "shop/api/views.py:36"}],
                     "reads": [{"file": "discounts", "at": "shop/pricing/discounts.py:20", "default": "0"}]}]}]}
```

- **parts** are the stated design's parts, in the direction dependencies may
  point, first to last. A file the design does not name has the part
  `outside`.
- **files** are the files that hold a decision site, a dependency, or a key
  a problem names. A picture of every file reads like none.
- **dependencies** have `today` and `proposed`, each *as stated*, *not
  stated*, *not found*, or `null` where it does not exist in that view.
- A file can carry the module change the plan proposes: `"renamed": "<new
  path>"`, `"removed": true`, or `"added": true` for a file the target
  creates. The proposal draws a renamed file under its new name and a
  removed one struck through; today draws a file to be added as an outline.
  A merge is files removed and one kept or added; a split is one removed
  and several added.
- **rules** are the rules the problems name, at most 26. `outcome` is
  *moves* (its sites go to the owner), *stays*, or *waits*. A site with
  `"waits": true` keeps its place until the user answers.
- **data** is one entry per piece of shapeless data a problem names.
- Every `at` is a pinned line, as `path.ext:12`, or starts with `proposed`.
  The check rejects one that is neither. A change card labels its views with
  `"labels": {"today": "Before", "proposed": "After the change"}`.

**A focus.** Under a problem, a `structure-focus` fence names part of that
data, and the page draws only that part, today and proposed side by side:

```json
{"rules": ["Loyalty discount rate"], "files": ["views"]}
```

`rules` are rule names and `files` are file ids of the structure view; the
files of the named rules come with them. A focus shows files and the
dependencies between them, so draw one when the problem spans files. A
problem that lives inside one file, such as one sequence copied into six
methods, is shown better by its excerpts side by side and a short table of
the copies, one row per copy and one column per step they differ in.

**A change history.** Under a problem whose evidence is history, such as a
rule that one change updated in some of its places and not others, a
`change-history` fence lists the places and the commits that changed them,
oldest first. Take them from `git log -L` on each place, or from
`change_coupling.py --functions`. The page draws one row per place and one
column per commit, and marks each place a commit left unchanged while
changing another; its caption counts those commits.

```json
{"rule": "Loyalty discount rate",
 "sites": [{"id": "discounts", "label": "pricing/discounts.py:12"},
           {"id": "builder", "label": "quotes/builder.py:27", "since": "3be62b3"}],
 "commits": [{"sha": "3be62b3", "date": "2023-02-17", "subject": "Quotes compute the discount", "changed": ["builder"]},
             {"sha": "93548a8", "date": "2023-09-01", "subject": "Raise gold to 10%", "changed": ["discounts"]}]}
```

`since` is the commit that created a place; before it the place did not
exist, and the commit that creates it is not counted as missing the others.

## The plan and the reference

*The plan* holds the recommended target and the user's choice, the structure
view, the target's modules, interface, boundary checks, data and state, flow,
failure behavior, and measure, then the module changes, the design
principles, the lock tests as a list, the steps, and questions that no
problem holds.

- **Modules** names each module of the target with its responsibility in one
  sentence with no *and*, its one reason to change, and the rules and state
  it owns.

- **Flow** states the one direction calls and state move in the target, in
  the order of the parts, and each edge against it that the target removes:
  a cycle, a call from a later part back to an earlier one, a callback or
  event through which a later step writes into an earlier one's state.
- **Module changes** is a list. Each item starts with **Rename**,
  **Remove**, **Merge**, **Split**, or **Move**, names the modules and what
  they become, labelled proposed, and gives the reason and the problems it
  removes. A name follows the decision the module owns in the project's
  words; a module with no decision of its own is removed or merged; a module
  that changes for two reasons is split. Draw each change in the structure
  view, as [pictures](#pictures) says.
- **Design principles** is a list of eleven items, one per principle of
  [clean structure](../../CLEAN-STRUCTURE.md), in its order. Each starts
  with the principle's name in bold, *Single responsibility*,
  *Open–closed*, *Liskov substitution*, *Interface segregation*,
  *Dependency inversion*, *YAGNI*, *Minimal shared state*, *One-way flow*,
  *Intention-revealing names*, *Readable functions*, or *Decisions with
  their data*, then today's result with its evidence and the
  proposed result. *Not applicable* with its reason is a result. The checker
  reads the names and requires all eleven. A lead reads this list to see what
  the rework buys: each principle broken today and met after is a reason to
  do it. *What is sound* lists what works and should
be kept, and what looks wrong and is fine, each with its reason.

*How it works today* is the reference the problems cite. Two tables keep
their columns exactly, because the checker reads them:

- **Stated design and the code.** Dependencies have *Result* one of *as
  stated*, *not stated*, *not found*, and *Evidence* names the edge source
  and pins the decisive file edges. Stated rules have *Result* one of
  *holds*, *broken*, *not checked*. When every dependency is as stated, one
  sentence with the count replaces the rows.
- **Special cases.** One row per classified case, with *Reach* one of
  *reached*, *not reached*, *unknown*, each followed by the caller, probe,
  or run that supports it. A case that is a problem names it in *Points to*.

State and data, and the deliberate breaks with their results, are lists and
prose; the features and the behavior no test protects are in *What it
does*. Every cell of a table has content, and an explicit unknown is
content; text that needs more than a line goes in a list instead.

## Names

Name a problem by its consequence and a target by its shape, such as
*Pricing owns discounts*. Use the project's glossary terms for features
and state. Steps are numbered in their list and referred to by what they do.

## Diagrams

A flow diagram shows what the source shows, labeled *source*, with the steps
a recorded run executed named in the sentence before it; a flow taken wholly
from a trace is labeled *observed*. A diagram of a target is *proposed*, and
every node and edge that does not exist yet is mapped as proposed. The source
map has one item per node and one per arrow. Keep the as-is diagram and the
target diagram of one flow in the same layout and names, so the reader sees
what moves.

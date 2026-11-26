# Rework map format

Read when filling or updating a rework map. The map is one note,
`rework-map.md`, written for a reader who was not there and who must be able
to check each claim quickly. Follow the [shared page workflow](../../HTML-PAGES.md)
for rendering, and [evidence](../../EVIDENCE.md) for every claim and diagram.

## Contents

- [Order and growth](#order-and-growth)
- [The opening](#the-opening)
- [Pins](#pins)
- [Tables](#tables)
- [Structure view](#structure-view)
- [Names](#names)
- [Diagrams](#diagrams)

## Order and growth

Keep the template's section order: what the user must decide comes before
the description, and the description before the proposal. The map grows
through the task: after step 2 it holds the opening, the questions, the
capability list, and the stated design; steps 3 and 4 add the census, the
tables, and the flows; steps 5 and 6 add findings, targets, and steps. Remove
a section that has nothing to hold or that the chosen deliverable does not
include, and say in *Limits and open questions* what was left out. A map
delivered at a checkpoint passes the check as it stands.

## The opening

The three bold lines under the title are what most readers read. Each states
its result and its scope: *What it does* in domain words; *What differs from
the stated design* with the count of dependencies and rules checked;
*Recommended rework* with one reason, or that the structure should stay as it
is. When the scope could not run, the *What ran* line says so first.

## Pins

Pin committed code at its commit. For a repository with a hosted remote,
build the link from `git remote get-url origin` and the inspected revision:
`[discounts.py:12](https://<host>/<owner>/<repo>/blob/<sha>/shop/pricing/discounts.py#L12)`.
With no hosted remote, link the path relative to the map with the same
anchor, and state the revision in the opening. Take line numbers from the
file at that revision.

## Tables

Use the template's column names exactly; the checker reads them. Every cell
has content, and an explicit unknown is content.

- **Behavior to decide.** One row per behavior that may be wrong or unwanted,
  worded as what a consumer sees, with the run that shows it and its handoff.
- **Questions for the user.** One row per question only a person can answer.
  *Default until answered* gives the conservative default and what changes
  under the other answer. *Answer* quotes the user, or says *open*. Keep
  answered rows: they are the record the next session reads.
- **Capabilities.** One row per capability, in the user's order of importance.
  A capability the code performs and no document or person named is marked
  *not stated anywhere*. Each inspected capability has its own section with
  one list item per decision site.
- **Stated design and the code.** Two tables. Dependencies have *Result* one
  of *as stated*, *not stated*, *not found*, and *Evidence* names the edge
  source and pins the decisive file edges. Stated rules have *Result* one of
  *holds*, *broken*, *not checked*. When every dependency is as stated, one
  sentence with the count replaces the rows.
- **State and data.** One row per piece of state, and one row per key of
  each piece of shapeless data, with the default each reader supplies. More
  than one writer is not yet a finding; it is what the user is shown.
- **Special cases.** One row per classified case, with *Reach* one of
  *reached*, *not reached*, *unknown*, each followed by the caller, probe, or
  run that supports it.
- **Lock tests.** One row per test written in step 7, with the break it
  failed under and the suite run that passed. Remove the section when the
  user chose no lock tests, and say so in the limits.
- **Findings.** One row per structure finding in rank order, with *Kind* one
  of *scattered rule*, *misplaced logic*, *needless link*, *surplus*, *shared
  mutable state*, *shapeless data*, *unjustified special case*. Each row links to its section.

## Structure view

The section *Structure today and proposed* holds one `structure-view` fence of
JSON. The page draws it: files grouped by design part, the dependencies
between them, a lettered dot for each place that decides a rule, a switch
between today and the proposal, and for shapeless data a table of who writes
and reads each key. Markdown readers see the JSON; the tables of the map
carry the same content as text. The sentence before the fence states the
takeaway and the evidence kind, as [evidence](../../EVIDENCE.md#diagrams)
says for a diagram.

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
  the findings name. Keep it to what the findings need; a picture of every
  file reads like none.
- **dependencies** have `today` and `proposed`, each *as stated*, *not
  stated*, *not found*, or `null` where it does not exist in that view.
- **rules** are the rules the findings name, at most 26. `outcome` is
  *moves* (its sites go to the owner), *stays*, or *waits*. A site with
  `"waits": true` keeps its place until the user answers.
- **data** is one entry per piece of shapeless data, from the *State and
  data* table.
- Every `at` is a pinned line, as `path.ext:12`, or starts with `proposed`.
  The check rejects one that is neither.

## Names

Name a finding by its consequence, such as *Discount rule decided in three
places*, and a target by its shape, such as *Pricing owns discounts*. Use the
project's glossary terms for capabilities and state. Steps are numbered in
their list and referred to by what they do.

## Diagrams

A flow diagram shows what the source shows, labeled *source*, with the steps
a recorded run executed named in the sentence before it; a flow taken wholly
from a trace is labeled *observed*. A diagram of a target is *proposed*, and
every node and edge that does not exist yet is mapped as proposed. The source
map has one item per node and one per arrow. Keep the as-is diagram and the
target diagram of one flow in the same layout and names, so the reader sees
what moves.

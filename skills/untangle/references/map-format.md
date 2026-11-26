# Rework map format

Read when filling or updating a rework map. The map is one note,
`rework-map.md`, written for a reader who was not there and who must be able
to check each claim quickly. Follow the [shared page workflow](../../HTML-PAGES.md)
for rendering, and [evidence](../../EVIDENCE.md) for every claim and diagram.

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
- **Findings.** One row per structure finding in rank order, with *Kind* one
  of *scattered rule*, *misplaced logic*, *needless link*, *surplus*, *shared
  mutable state*, *shapeless data*, *unjustified special case*. Each row links to its section.

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

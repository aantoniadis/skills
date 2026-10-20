# Review report format

## Contents

- [Shape](#shape)
- [Shared parts](#shared-parts)
- [Part shape](#part-shape)
- [Diagrams](#diagrams)
- [Chat reply](#chat-reply)
- [Page](#page)
- [Final structural check](#final-structural-check)

Read when writing or updating `report.md` or the chat reply. The page renders these shapes as components; other Markdown readers see plain headings, lists, and fences. `render_page.py --check --review` checks the current report structure, table statuses, required links, and evidence origins as well as the shared page checks. It checks recorded structure, not whether an investigation happened or a conclusion is correct; the second reader checks meaning.

For a new report, fill [report-template.md](report-template.md). Replace every prompt, repeat attention items and parts as needed, and remove optional sections under the conditions below. This format remains authoritative; update an existing report in place.

## Shape

Say each fact once, in the section where the reader acts on it; every other mention links there. A section appears only when it adds something. Use these headings as written, because the checks and the page look for them:

- **Title** — `# <what the change does, as a short statement>`.
- **Bottom line** — the paragraph right under the title, starting `**Bottom line:**`: in one or two sentences, about 50 words, the supported review conclusion, established blockers, remaining decisions, and what the reviewer checks first. Keep consequential coverage limits beside the conclusion. This is review context, not approval or a guarantee that all defects were found.
- **Reviewed and coverage** — an opening paragraph beginning `**Reviewed:**` names head, base, and merge base; `**Coverage:**` states the depth reached and consequential uninspected areas. Detailed provenance stays in the record.
- `## What the change does` — for a reader who has not seen the PR: the problem it addresses, the intent as stated (quoted, with its link) or inferred (labeled), and what a caller or user notices afterwards. Then say what moved, the tradeoff it makes, the contract that now matters, and the strongest supported case for it — documented rationale quoted, inference labeled. About 150 words for a one-part change; two short paragraphs for a large one.
- `## Terms` — only when the change introduces or repurposes a domain term: term → one-line meaning → where it lives, each a pinned link. Audience sets the depth of mechanism, never the vocabulary.
- `## What to look at` — every item that merits attention, in the item shape below, ranked by the consumer's next action if the item is wrong; no minimum and no maximum. One tight ordered list, no blank lines or subheadings inside it, with the read-lightly and no-action items last.
- `## Possible bugs` — always present, right after *What to look at*: the not-run sentence, the none-found sentence, or one card per bug, as [bug cards](../../REPORT-PARTS.md#bug-cards) says.
- `## Requirements` — the visible fulfillment table described below, with intent sources and links to named behavior sections.
- `## Reading plan` — only when the change touches more than about eight files: every changed file in exactly one lens, nothing left out, in the order a reviewer should open them. Use **Read**, **Skim**, or **Skip** according to the change's consequences and the evidence needed, with files in useful reading order. Tests, configuration, docs, generated output, and lockfiles can define the main behavior or contract. Give a scope-based reason for each skipped group; file type alone does not justify skipping it. Each file is a pinned link. It replaces *Changed files* in the record.
- `## Behavior changes` — one `###` subsection per consequential **named behavior**, in the order a user meets it. Use the part shape below, including for a single consequential part; the opening summarizes and links here. If inspection found no consequential behavior change, state `No consequential behavior change:` with the inspected scope and supporting evidence. An early overview can instead state `Not yet inspected:` and name the boundary still to inspect.
- `## Questions for the author` — the questions only the author can answer and the choices the author must confirm, one line each: the question and a link to its item, or to its bug card when it comes from a bug, whose evidence it does not repeat. Link a relevant attention item, bug card, or behavior section. If no author decision remains, state none with the scoped reason. Prepare a PR comment only when requested.
- `## Verification` — the visible check table described below, with inspected assertions, recorded runs, and executions during this review distinguished.
- `## Evidence and record` — supporting **Gaps**, **Changed files** (part and inspection status for every changed file, unless the reading plan covers them), and **Provenance** (head, base, merge base, observed base tip, collection and intent-source read times, local modifications, prior reviews). Each record subsection contains evidence or an explicit none/unknown. The page collapses this detail; consequential gaps also remain beside the affected conclusion.

## Shared parts

Attention items, the requirements and verification tables, bug cards, and
links, code cards, and citations follow [report parts](../../REPORT-PARTS.md).

## Part shape

For each named behavior, fill [behavior-template.md](behavior-template.md). Keep its named heading stable so requirements, findings, and verification can link to it. A short part can fit in a few paragraphs and one scenario row; omit optional material that adds no review value.

- **Purpose and tradeoff** — the problem and documented rationale (quoted and linked) or labeled inference, the benefit, and what it gives up.
- **Conditions** — actor, input, configuration, existing state, and the trigger for the change.
- **Scenario table** — Scenario, Before, After, Consumer consequence, Evidence. Walk the same scenario at base and head through the affected consumer's next action. Cover meaningful success, rejection, failure, interruption, retry, and state boundaries from the inspected flow; keep unknowns explicit. Use pinned base/head lines or applicable run records, not test names alone.
- **Decisive excerpt** — show a changed endpoint, payload, status code, signature, or contract as a `diff` code card. Keep the relevant failure branch and unchanged context needed to understand it.
- **Path or diagram**, when it answers a reading question — follow the entry point through unchanged producers and consumers to the consequence. Keep relevant guards, asynchronous boundaries, and alternate paths. Apply the diagram guidance below.
- **Consumers** — affected callers, the contract they rely on, their next action, compatibility evidence, and required adaptation. Use a consumer table for multiple consumers or a public boundary. Compare a new consumer with the existing consumers of the same producer, including output fields, cleanup, authorization, and partial-success signals. Label inferred external usage and its limits.
- **Preserved** — relevant unchanged behavior and its evidence or gap.
- **Depends on**, when relevant — assumptions, protections, and where they are enforced or remain unverified.
- **Deployment**, when relevant — mixed-version behavior, migration/backfill, flag defaults, rollback after writes, and signals that distinguish completion from partial failure. Include only concerns the change creates or affects.
- **Open question** — what evidence or author decision would change the conclusion; an explicit none needs a scoped reason. Links to the attention items carry actions; questions only the author can answer also appear in *Questions for the author*.

A finding names its trigger, consequence, consumer, decisive evidence, and settling check or decision. Show **Resolution:** only when relevant to a follow-up: Open, Resolved with linked evidence, or Accepted tradeoff with the decision maker and record. Acceptance does not change a requirement's fulfillment status. On a new head, recheck affected findings before carrying their resolution forward.

A representative edit can explain a part. *Equivalent*, *mechanical*, *covered by tests*, *safe to skim*, and a read-lightly item for a whole part each need evidence covering every member and the relevant preservation claim; an uninspected file gets none. Items are those that change the reviewer's action; call-site sweeps and evidence tables go in disclosures; about 400 words of prose per part is the guide, not a cap — a part that reads better with more keeps them; cut repetition and mechanism the linked code shows, never a consequence.

## Diagrams

Choose a diagram when it answers a question that the scenario table, prose, or diff leaves hard to follow:

| Question | Visual |
| --- | --- |
| Where does the change sit? | Small context or call-path diagram from the entry point. |
| What happens in what order across components? | Sequence diagram, including relevant failure, cancellation, and cleanup boundaries. |
| Which condition selects an outcome? | Flowchart or decision table. |
| Which states and transitions become possible? | State diagram. |
| What data changes, and who uses it? | Mermaid `erDiagram` plus a table naming readers and writers of changed tables. |
| Does a measured performance claim hold? | Chart of comparable base/head measurements with units, workload, configuration, repetitions, and variation; link the raw results. |

Place the visual beside the behavior it explains. Keep the same names and layout in before/after views; mark added, removed, and changed steps with text or line style as well as color. Keep necessary unchanged guards and branches. Every diagram has a takeaway, an observed/source/proposed label, and the complete node/edge source map required by [EVIDENCE.md](../../EVIDENCE.md). Use base lines for removed steps and head lines for current ones. Its text explanation remains complete in Markdown and without JavaScript. Missing source support stays an explicit gap, not an invented edge.

Keep a sequence focused on one reading question. When a large combined diagram
becomes hard to read, split ordering, lifecycle, or base/head comparison into
separate views beside the relevant behavior. State which paths each view covers
and retain consequential alternatives in another view or the scenario table.
Label explanatory states as proposed models when the code has no such states;
distinguish server completion from the consumer's recognition of the result.

A chart visualizes recorded measurements, not guessed precision. A model or fictional example is labeled throughout and establishes no real-system result. Choose a diagram when it answers a consequential ordering, state, or data-flow question more clearly than prose or a table. Do not add a diagram quota or repeat a trivial table as a graph.

## Chat reply

Deliver after integrating findings and running the final structural check. Lead with the supported conclusion or the answer to the follow-up question. Include the consequential findings, checked report link, and material evidence limits at the length the request needs. For an overview, identify uninspected scope. Reuse settled choices. The first delivery carries a `Kickoff:` line naming the applied choices, supplied or defaulted: familiarity, deliverable, depth, and search for bugs ([asking](../../ASKING.md)). Suggest further questions only when they would help the reviewer; there is no fixed count. The reply adds no claim absent from the report.

## Page

The page shows the what-to-do and how-we-know phrases as chips, ranked findings with separate Look at and Settle rows, fences with `url` as code cards, every fence with a language highlighted and a cited fence numbered from its `#L` start, links to files under the report directory such as probe scripts and their output opened in the code peek with copy buttons, named behaviors nested in navigation, requirement and verification status badges, and *Evidence and record* collapsed. The reading plan's items are grouped under Read, Skim, and Skip, each item's reason beside its file links as chips. Scenario tables become named comparisons: Before and After sit side by side on wide screens and stack on narrow ones; Consumer consequence and Evidence use the full width below. Requirement and verification tables reflow into labeled rows on narrow screens. Requirements, verification, blockers, and material limits remain visible; supporting traces can collapse. Navigation mirrors the part names; long traces and evidence tables sit in disclosures on the page while the Markdown keeps them open.

## Final structural check

Before every report delivery, run `python3 <package>/skills/render_page.py <report.md> --check --review --sync-labels` after the last edit, including for text-only delivery and follow-up updates. Repair structural failures and rerun the check before presenting the report as complete. If the checker cannot run, state that blocker and label the report structurally unchecked. Use `--review` when rendering a companion in this format. The validator checks declared snapshot syntax, opening scope, required sections and record subsections, tables and statuses, behavior fields and scenario comparisons, linked evidence, and local anchors. A supplied `base` or `head` must be a full commit SHA and `repository` must be `owner/name`; syntax does not establish commit availability. Local or inaccessible snapshots need explicit source identity and gaps in Provenance. Unfilled template prompts fail validation. Keep all content consistent between Markdown and HTML, including on custom pages. The shared page workflow checks a source fingerprint to detect a companion made from older Markdown; custom composition still needs meaning review.

For a text-only delivery, add `--markdown-only` to that command, retaining
`--check --review --sync-labels`. This checks the current report independently
of a deferred HTML companion. Record that companion as stale and do not present
it. Reconcile it and check without `--markdown-only` before delivering HTML.

The check cannot establish scenario completeness, correct status judgments, trace fidelity, actual execution, or review quality. The author or an optional second reader follows requirement → behavior → evidence → action to check those meanings. An overview reply labels incomplete investigation instead of filling it with invented results.

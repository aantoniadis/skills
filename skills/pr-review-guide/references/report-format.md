# Review report format

## Contents

- [Shape](#shape)
- [Requirements and verification tables](#requirements-and-verification-tables)
- [Item shape](#item-shape)
- [Bug cards](#bug-cards)
- [Part shape](#part-shape)
- [Links, code cards, citations](#links-code-cards-citations)
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
- `## Possible bugs` — always present, right after *What to look at*: the not-run sentence, the none-found sentence, or one card per bug, as [Bug cards](#bug-cards) says.
- `## Requirements` — the visible fulfillment table described below, with intent sources and links to named behavior sections.
- `## Reading plan` — only when the change touches more than about eight files: every changed file in exactly one lens, nothing left out, in the order a reviewer should open them. Use **Read**, **Skim**, or **Skip** according to the change's consequences and the evidence needed, with files in useful reading order. Tests, configuration, docs, generated output, and lockfiles can define the main behavior or contract. Give a scope-based reason for each skipped group; file type alone does not justify skipping it. Each file is a pinned link. It replaces *Changed files* in the record.
- `## Behavior changes` — one `###` subsection per consequential **named behavior**, in the order a user meets it. Use the part shape below, including for a single consequential part; the opening summarizes and links here. If inspection found no consequential behavior change, state `No consequential behavior change:` with the inspected scope and supporting evidence. An early overview can instead state `Not yet inspected:` and name the boundary still to inspect.
- `## Questions for the author` — the questions only the author can answer and the choices the author must confirm, one line each: the question and a link to its item, or to its bug card when it comes from a bug, whose evidence it does not repeat. Link a relevant attention item, bug card, or behavior section. If no author decision remains, state none with the scoped reason. Prepare a PR comment only when requested.
- `## Verification` — the visible check table described below, with inspected assertions, recorded runs, and executions during this review distinguished.
- `## Evidence and record` — supporting **Gaps**, **Changed files** (part and inspection status for every changed file, unless the reading plan covers them), and **Provenance** (head, base, merge base, observed base tip, collection and intent-source read times, local modifications, prior reviews). Each record subsection contains evidence or an explicit none/unknown. The page collapses this detail; consequential gaps also remain beside the affected conclusion.

## Requirements and verification tables

Use the template's column names. Every cell has content; an explicit unknown or a reasoned non-applicability is useful content. Remove unused prompt rows. Requirements link to their intent source and a named behavior section; that section links to decisive source or run evidence and relevant attention items. Say a fact once and link to it elsewhere.

Requirement statuses come from the shared [label catalog](../../report-labels.json);
`--sync-labels` writes their key into the report.

Work in both directions: intent to behavior, then consequential delivered behavior to intent. An extra effect with no supporting intent stays intent-unconfirmed in the surrounding text or a Needs clarification row. A necessary implementation detail does not by itself establish scope creep. When no spec is accessible, use explicitly inferred candidates and name the missing intent; never invent a quoted requirement. Counts may summarize rows but do not decide readiness. Fulfillment, consequence, evidence kind, and finding resolution are separate judgments.

The verification table uses **Result**: Passed, Failed, Mixed, Not run, or Blocked; and **Evidence origin**: Executed here, Recorded run, Source inspected, or Proposed. Source inspected uses Not run. Proposed uses Not run, or Blocked when preparation could not complete; name the obstruction and any retained evidence. Reading an assertion or proposing a test does not establish execution. An executed or recorded result links to its run record and states revision, configuration, and limits. Unknown CI conditions limit applicability. If no checks were selected, write `No checks selected:` and the reason above a table holding only *Bug probes*; retain `Tests inspected:`, `Recorded runs:`, and `Executed:` with explicit none where appropriate.

One *Bug probes* row links to `#possible-bugs`. Its result and origin describe actual checks, separately from whether the search found a defect:

- Search not run: Not run / Proposed, or Blocked / Proposed when preparation failed.
- Source-only search: Not run / Source inspected, including when no bugs were found.
- Executed or reused checks: the actual Passed, Failed, Mixed, or Blocked result, with Executed here or Recorded run. Link a run record in the check cell when no executed bug card supplies it. An executed check can refute a hypothesis while another finding remains suspected.
- A *we ran it* card requires execution evidence, with the actual check result. A diagnostic can pass by observing the predicted defect; an assertion of the required application behavior can fail on that same observation. State the expected outcome and what happened. For Blocked, name the obstruction and distinguish retained observations from unfinished checks. Use Executed here for execution in this session, including delegated execution. When resuming a guide, preserve earlier observed cards and use Recorded run with a link to the original run record, its date, snapshot, and conditions. That card refers to the earlier execution, not a fresh run. External reported defects remain attributed evidence in the behavior explanation and Verification until verified; retain uncertainty about their applicability.

The scope cell names checks performed, remaining suspicions, and material limits. A none-found paragraph reports the bounded search outcome, not a passing runtime result.

For each named behavior, expose decisive scenario comparisons; use a larger matrix in the review record when interactions warrant it, with results and named untested gaps. Select scenarios from inspected control flow using [behavior comparison](../../BEHAVIOR-COMPARISON.md), including common configurations. Link checks back to those scenarios. Distinguish new defects, pre-existing defects, and old defects made consequential by this change.

## Item shape

```
1. **<the consequence, as a short title>** — *<what to do>* · *<how we know>*
   <one or two sentences: what changed and what follows, with the decisive evidence>
   Look at: [pinned link], and what to hold beside it ([pinned link]).
   Settle: <the question that decides it>
```

Keep Look at and Settle on their own indented lines so the page can give each a visible label. Write concise sentences, but retain context, conditions, and evidence limits even when they need more space; never shorten a claim just to fit a column.

The title names the consequence — *Duplicates no longer count* — not the location. The text under it is one or two sentences, about 60 words: what changed and what follows, with the decisive result ("we ran it: 3 before, 2 after"). Commands and full output go to the run record linked from *Verification*, or for a bug to its card. **What to do**, one phrase: *you decide* (a choice is the reviewer's or the author's), *check it* (a claim to confirm at the code or by a run), *ask the author* (only the author can answer), *read lightly* (the evidence covers the whole part), *no action* (known, nothing to do today). **How we know**, one phrase for each kind in [EVIDENCE.md](../../EVIDENCE.md): *we ran it* (an executed or measured run; a retained earlier card names its original run in Verification), *read at the line* (read at the pinned lines), *documented* (quoted intent), *reasoned, not run* (inferred), *not read* (not inspected), *unknown*. Apart from a bug's item, below, a you-decide, check-it, or ask-the-author item carries *Look at* and *Settle*; a read-lightly item rests on *we ran it* or *read at the line* evidence covering every member of its part. With several parts, the item names its part.

Each card has exactly one item. An item for a bug is one concise line: its title, what to do (*you decide* or *check it*), the evidence phrase that matches its card's chip — *we ran it* for a *we ran it* card, *reasoned, not run* for a *suspected, not run* card — and a link to the card's heading anchor, such as `[details](#1-overridden-dependencies-stay-in-memory)`. The card holds the detail and the reading route, so the item carries no *Look at* or *Settle*.

## Bug cards

`## Possible bugs` holds exactly one of three forms:

- **Not run** — one paragraph starting `The search for bugs has not run:`, then the reason: the review stopped at the overview, the user stopped or skipped the search, or its worker failed.
- **None found** — one paragraph starting `No bugs found:`, then the inspected paths, checks or probes, and material limits; distinguish source inspection from execution.
- **Cards** — one `###` card per bug the search for bugs returned, numbered `1.`, `2.`, … in rank order by impact, reach and likelihood, recoverability, and confidence. Explain the affected consumer's next action; neither silent errors nor loud failures have automatic priority. The heading names the consequence, as an item title does. A ruled-out hypothesis gets no card.

Keep the not-run and none-found forms to one concise paragraph, and each bug's attention item to one concise line. The checker validates that structure without counting punctuation as sentences.

A card holds only these lines, in this order; [report-template.md](report-template.md) shows the layout. Detail that fits no field goes in the part the bug affects.

1. **Chip line**, the whole first line under the heading: the evidence chip, *we ran it* (a probe ran at the head; a reused card retains the original run provenance) or *suspected, not run* (reasoned; no probe ran), then ` · ` and the origin chip, *new in this change* or *pre-existing, made worse* (the line predates this change, and the change reaches it from a new path or worsens its result).
2. `**Where:**` — at least one pinned line; the page opens it in the code peek.
3. `**Trigger:**` — the input, configuration, or caller that reaches the bug.
4. **Base/Head table** — a label column, then exactly `Base` and `Head`, one filled row per compared result. On a *suspected, not run* card, every Base and Head cell starts with `predicted:`, because no run observed it. On a *we ran it* card, every Head cell is observed; a Base value that no run observed, because the base could not run, starts with `predicted:`.
5. `**Who / impact:**` — the affected consumers and what they see, with its basis: a pinned line, or the label *reasoned, not run* or `predicted:` when no line or run shows it.
6. `**Fix direction:**` — starts with *Suggestion:*; the author chooses the fix.
7. For *we ran it*: `**Reproduce:**`, then one code fence with the exact command, which names the probe script's path, then one `Output:` line that holds only the output excerpt as inline code and a link to the probe script under the report's `runs/bugs/`, joined by ` · `. For *suspected, not run*: `**Probe that would settle it:**` with the probe on the same line, or as one code fence after an empty field line.

Each value carries its evidence as [EVIDENCE.md](../../EVIDENCE.md) says: a pinned line for a code fact, the reproduction for an observed result, `predicted:` for a suspected one.

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

## Links, code cards, citations

- Use a short excerpt or labeled pseudocode when it helps explain the decisive behavior. Link the full source; length alone does not require a summary.
- Every mention of a file or symbol outside *Provenance* links to the pinned line at head at least once per subsection: `[contentVisibility.ts:98](https://github.com/<owner>/<repo>/blob/<head-sha>/backend/src/services/contentVisibility.ts#L98)`. A bare `path:line` is not a reference, because the report is read on the page and on GitHub. When the snapshot is a local directory, link the relative path with the same anchor — link text `service.py:17`, link target `head/orders/service.py#L17`. Take line numbers from the head file itself, never from diff-hunk arithmetic.
- A you-decide or check-it item, or one that contradicts or only partly matches the stated intent, shows its decisive hunk — about fifteen lines at most — as a fence whose info string carries the pinned link: ```` ```ts url="https://github.com/<owner>/<repo>/blob/<head-sha>/path#L60-L72" ````. The fence sits in the named behavior section because the list of items stays compact. A changed contract or function body shows as a `diff` fence with the same attribute.
- Quote each requirement with its specific source in the requirements table, for example `"404, never 403" ([#252](https://github.com/<owner>/<repo>/issues/252))`. Later mentions name the requirement and link its source or report section; repeat the quote only when its exact wording matters. Preserve qualifications and keep inferred requirements distinct from quoted intent.

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

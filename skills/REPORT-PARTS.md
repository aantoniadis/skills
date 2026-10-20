# Report parts

Read when writing an attention item, a requirements or verification table, a
bug card, or a citation in a pr-review-guide or check-acceptance report. Each
skill's report format names its own sections and order; these parts are the
same in both.

## Contents

- [Requirements and verification tables](#requirements-and-verification-tables)
- [Item shape](#item-shape)
- [Bug cards](#bug-cards)
- [Links, code cards, citations](#links-code-cards-citations)

## Requirements and verification tables

Use the template's column names. Every cell has content; an explicit unknown or a reasoned non-applicability is useful content. Remove unused prompt rows. Requirements link to their intent source and a named behavior section; that section links to decisive source or run evidence and relevant attention items. Say a fact once and link to it elsewhere.

Requirement statuses come from the shared [label catalog](report-labels.json);
`--sync-labels` writes their key into the report.

Work in both directions: intent to behavior, then consequential delivered behavior to intent. An extra effect with no supporting intent stays intent-unconfirmed in the surrounding text or a Needs clarification row. A necessary implementation detail does not by itself establish scope creep. When no spec is accessible, use explicitly inferred candidates and name the missing intent; never invent a quoted requirement. Counts may summarize rows but do not decide readiness. Fulfillment, consequence, evidence kind, and finding resolution are separate judgments.

The verification table uses **Result**: Passed, Failed, Mixed, Not run, or Blocked; and **Evidence origin**: Executed here, Recorded run, Source inspected, or Proposed. Source inspected uses Not run. Proposed uses Not run, or Blocked when preparation could not complete; name the obstruction and any retained evidence. Reading an assertion or proposing a test does not establish execution. An executed or recorded result links to its run record and states revision, configuration, and limits. Unknown CI conditions limit applicability. If no checks were selected, write `No checks selected:` and the reason above a table holding only *Bug probes*; retain `Tests inspected:`, `Recorded runs:`, and `Executed:` with explicit none where appropriate.

One *Bug probes* row links to `#possible-bugs`. Its result and origin describe actual checks, separately from whether the search found a defect:

- Search not run: Not run / Proposed, or Blocked / Proposed when preparation failed.
- Source-only search: Not run / Source inspected, including when no bugs were found.
- Executed or reused checks: the actual Passed, Failed, Mixed, or Blocked result, with Executed here or Recorded run. Link a run record in the check cell when no executed bug card supplies it. An executed check can refute a hypothesis while another finding remains suspected.
- A *we ran it* card requires execution evidence, with the actual check result. A diagnostic can pass by observing the predicted defect; an assertion of the required application behavior can fail on that same observation. State the expected outcome and what happened. For Blocked, name the obstruction and distinguish retained observations from unfinished checks. Use Executed here for execution in this session, including delegated execution. When resuming a guide, preserve earlier observed cards and use Recorded run with a link to the original run record, its date, snapshot, and conditions. That card refers to the earlier execution, not a fresh run. External reported defects remain attributed evidence in the behavior explanation and Verification until verified; retain uncertainty about their applicability.

The scope cell names checks performed, remaining suspicions, and material limits. A none-found paragraph reports the bounded search outcome, not a passing runtime result.

For each named behavior, expose decisive scenario comparisons; use a larger matrix in the review record when interactions warrant it, with results and named untested gaps. Select scenarios from inspected control flow using [behavior comparison](BEHAVIOR-COMPARISON.md), including common configurations. Link checks back to those scenarios. Distinguish new defects, pre-existing defects, and old defects made consequential by this change.

## Item shape

```
1. **<the consequence, as a short title>** — *<what to do>* · *<how we know>*
   <one or two sentences: what changed and what follows, with the decisive evidence>
   Look at: [pinned link], and what to hold beside it ([pinned link]).
   Settle: <the question that decides it>
```

Keep Look at and Settle on their own indented lines so the page can give each a visible label. Write concise sentences, but retain context, conditions, and evidence limits even when they need more space; never shorten a claim just to fit a column.

The title names the consequence — *Duplicates no longer count* — not the location. The text under it is one or two sentences, about 60 words: what changed and what follows, with the decisive result ("we ran it: 3 before, 2 after"). Commands and full output go to the run record linked from *Verification*, or for a bug to its card. **What to do**, one phrase: *you decide* (a choice is the reviewer's or the author's), *check it* (a claim to confirm at the code or by a run), *ask the author* (only the author can answer), *read lightly* (the evidence covers the whole part), *no action* (known, nothing to do today). **How we know**, one phrase for each kind in [EVIDENCE.md](EVIDENCE.md): *we ran it* (an executed or measured run; a retained earlier card names its original run in Verification), *read at the line* (read at the pinned lines), *documented* (quoted intent), *reasoned, not run* (inferred), *not read* (not inspected), *unknown*. Apart from a bug's item, below, a you-decide, check-it, or ask-the-author item carries *Look at* and *Settle*; a read-lightly item rests on *we ran it* or *read at the line* evidence covering every member of its part. With several parts, the item names its part.

Each card has exactly one item. An item for a bug is one concise line: its title, what to do (*you decide* or *check it*), the evidence phrase that matches its card's chip — *we ran it* for a *we ran it* card, *reasoned, not run* for a *suspected, not run* card — and a link to the card's heading anchor, such as `[details](#1-overridden-dependencies-stay-in-memory)`. The card holds the detail and the reading route, so the item carries no *Look at* or *Settle*.

## Bug cards

`## Possible bugs` holds exactly one of three forms:

- **Not run** — one paragraph starting `The search for bugs has not run:`, then the reason: the review stopped at the overview, the user stopped or skipped the search, or its worker failed.
- **None found** — one paragraph starting `No bugs found:`, then the inspected paths, checks or probes, and material limits; distinguish source inspection from execution.
- **Cards** — one `###` card per bug the search for bugs returned, numbered `1.`, `2.`, … in rank order by impact, reach and likelihood, recoverability, and confidence. Explain the affected consumer's next action; neither silent errors nor loud failures have automatic priority. The heading names the consequence, as an item title does. A ruled-out hypothesis gets no card.

Keep the not-run and none-found forms to one concise paragraph, and each bug's attention item to one concise line. The checker validates that structure without counting punctuation as sentences.

A card holds only these lines, in this order; each skill's report template shows the layout. Detail that fits no field goes in the part the bug affects.

1. **Chip line**, the whole first line under the heading: the evidence chip, *we ran it* (a probe ran at the head; a reused card retains the original run provenance) or *suspected, not run* (reasoned; no probe ran), then ` · ` and the origin chip, *new in this change* or *pre-existing, made worse* (the line predates this change, and the change reaches it from a new path or worsens its result). *from an unrelated commit* and *no base pinned* belong to acceptance reports; a PR review always pins a base and never uses *no base pinned*.
2. `**Where:**` — at least one pinned line; the page opens it in the code peek.
3. `**Trigger:**` — the input, configuration, or caller that reaches the bug.
4. **Base/Head table** — a label column, then exactly `Base` and `Head`, one filled row per compared result. On a *suspected, not run* card, every Base and Head cell starts with `predicted:`, because no run observed it. On a *we ran it* card, every Head cell is observed; a Base value that no run observed, because the base could not run, starts with `predicted:`.
5. `**Who / impact:**` — the affected consumers and what they see, with its basis: a pinned line, or the label *reasoned, not run* or `predicted:` when no line or run shows it.
6. `**Fix direction:**` — starts with *Suggestion:*; the author chooses the fix.
7. For *we ran it*: `**Reproduce:**`, then one code fence with the exact command, which names the probe script's path, then one `Output:` line that holds only the output excerpt as inline code and a link to the probe script under the report's `runs/bugs/`, joined by ` · `. For *suspected, not run*: `**Probe that would settle it:**` with the probe on the same line, or as one code fence after an empty field line.

Each value carries its evidence as [EVIDENCE.md](EVIDENCE.md) says: a pinned line for a code fact, the reproduction for an observed result, `predicted:` for a suspected one.

## Links, code cards, citations

- Use a short excerpt or labeled pseudocode when it helps explain the decisive behavior. Link the full source; length alone does not require a summary.
- Every mention of a file or symbol outside *Provenance* links to the pinned line at head at least once per subsection: `[contentVisibility.ts:98](https://github.com/<owner>/<repo>/blob/<head-sha>/backend/src/services/contentVisibility.ts#L98)`. A bare `path:line` is not a reference, because the report is read on the page and on GitHub. When the snapshot is a local directory, link the relative path with the same anchor — link text `service.py:17`, link target `head/orders/service.py#L17`. Take line numbers from the head file itself, never from diff-hunk arithmetic.
- A you-decide or check-it item, or one that contradicts or only partly matches the stated intent, shows its decisive hunk — about fifteen lines at most — as a fence whose info string carries the pinned link: ```` ```ts url="https://github.com/<owner>/<repo>/blob/<head-sha>/path#L60-L72" ````. The fence sits in the named behavior section because the list of items stays compact. A changed contract or function body shows as a `diff` fence with the same attribute.
- Quote each requirement with its specific source in the requirements table, for example `"404, never 403" ([#252](https://github.com/<owner>/<repo>/issues/252))`. Later mentions name the requirement and link its source or report section; repeat the quote only when its exact wording matters. Preserve qualifications and keep inferred requirements distinct from quoted intent.


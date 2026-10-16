# Shared reading pages

Read this when filling, checking, or rendering an understanding note, behavior
plan, PR review, or bug diagnosis. Apply [technical English](TECHNICAL-ENGLISH.md). Markdown
remains authoritative for findings, source excerpts, evidence, and decision status.

## Contents

- [Fill the content, then render](#fill-the-content-then-render)
- [Explain report labels](#explain-report-labels)
- [Compose the content](#compose-the-content)
- [Check mechanics and meaning separately](#check-mechanics-and-meaning-separately)
- [Check the page](#check-the-page)

## Fill the content, then render

For a new note, start from the calling skill's Markdown template:

| Content | Starting point | Rules |
| --- | --- | --- |
| Code explanation | [understanding-template.md](explain/references/understanding-template.md) | [Reading-page guidance](explain/references/reading-page.md) and the calling skill |
| Behavior plan | [plan-template.md](plan-change/references/plan-template.md) | [Planning-page guidance](plan-change/references/planning-page.md) and the calling skill |
| PR review | [report-template.md](pr-review-guide/references/report-template.md) | [Report format](pr-review-guide/references/report-format.md) |
| Bug diagnosis | [diagnosis-template.md](fix-bug/references/diagnosis-template.md) | [Diagnosis-page guidance](fix-bug/references/diagnosis-page.md) and the calling skill |

Replace every `{{...}}` prompt with supported content. Repeat items and sections
when the subject needs them; remove optional sections that add nothing. The
calling skill's obligations and evidence rules still apply. A template starts
the document; it neither proves completeness nor requires empty sections.
Update an existing note in place instead of replacing it with the template.

For HTML delivery, generate the companion from the authoritative Markdown with
`python3 <resolved-script-path> <note.md> --sync-labels [--repo <checkout>]`, with `--review` for a PR review, using [render_page.py](render_page.py)
beside this reference in the installed package. The renderer fills
[page-template.html](page-template.html); it owns typography, spacing, colors,
navigation, tables, code cards, and disclosures. Choose the reading order and
leading visual in Markdown, then regenerate HTML after content changes.
Reuse the template's warm light palette, embedded typeface, and responsive
components unless the user requests another style. Put report-specific content
in Markdown; shared presentation changes belong in the template and diagram
theme, not in generated HTML.
For diagrams, select and record the backend as [RENDERER.md](RENDERER.md#optional-diagram-renderer) describes.

Render after the last edit to the Markdown and to every local file it links,
then check. The page embeds those files, so a run log or record edited after
the render, even to note the check's own result, fails the check; keep such
results in a file the note does not link, or render and check again.

Each template's page guidance defines the meaning of its fields and tables.
The checker compares those tables with Markdown, including their owning
sections and links; it validates the declared rows, not whether the author
captured every user question or decision, and does not judge the status
choices. The same checks run for Markdown-only delivery.

## Explain report labels

Every report explains the available values for each status or label family it uses,
including values absent from its rows. The shared [label catalog](report-labels.json)
defines requirement fulfillment, verification results and origins, decisions,
question coverage, review actions and evidence, intent alignment, finding resolution,
reading depth, and diagram evidence. Keep these judgments distinct: Partial has a
different meaning for a requirement and a learning question; agreement and passing
checks do not establish overall readiness.

`--sync-labels` fills or refreshes the reserved `## Status and label key` section
in Markdown from the families detected in the report. It preserves the report body
and keeps the definitions portable. Every render and check command includes it. With `--check`, it rewrites only the Markdown key, and only when every
check passes; a `--check` without it changes neither file and rejects missing or
stale definitions. A companion whose key no longer matches the Markdown fails the
check: regenerate it with the same diagram backend and `--sync-labels`, then check it.
A custom page is not regenerated: update its key section to match the Markdown,
then check it.

HTML places help links beside status tables, review actions, and diagrams. They
open the complete key; native disclosures keep it readable without JavaScript and
print exposes the definitions. Explain custom domain statuses next to their use in
ordinary report text. Keep custom meanings outside the generated key so refreshing
it cannot discard them. Use an explicit Resolution label for finding-resolution
states so the renderer can select their full vocabulary.

Before regenerating an existing companion, inspect it and its assets. Preserve
useful anchors and any explicitly requested interaction. Use custom HTML only
when an explicitly requested interaction cannot be represented by the existing
renderer components. Record that exception and its reason in the review record;
validate it with `--check` instead of rendering over it. Custom pages retain the
same portability, accessibility, evidence, and meaning checks below.

## Compose the content

Make the opening readable in about 30 seconds: answer the reader's central
question, state the consequence, and point to the next reading step. Keep scope
and qualifications that change the answer visible here; put supporting detail
below. A walkthrough can lead with a sequence diagram, a plan with a comparison
table, and a review with ranked attention priorities. Choose a leading visual
when it answers the question; its labels and visual distinctions carry meaning
supported by the source or explicitly identify a proposed model.

Use prose and simple lists for ordinary explanation. Reserve cards for findings,
decisions, or source excerpts, and chips for meaningful action or evidence
status. Use spacing and heading levels to separate decisions from evidence.
Omit empty optional sections and their headings; retain explicit unknowns and
evidence gaps that affect the answer. Reuse an existing component before writing
another; extract new shared code when another page needs it.

Collapse long traces or inventories when that improves reading; keep a comparison
or short explanation open when the reader needs it. Heading order, blockquotes,
and disclosures are composition choices, not a required Markdown schema.

Update Markdown first. The HTML can reorganize content and repeat labels in a
diagram. Retain all material findings, conditions, source excerpts, references,
and uncertainties. Add a diagram's text explanation and evidence label to Markdown.
Keep proposed behavior, agreement, source inference, and runtime evidence distinct.
Preserve useful anchors as the report develops.

Deliver one portable HTML file with styles, diagrams, and required scripts inline.
The renderer embeds the bundled Manrope font and its license. The shared
[diagram theme](diagram-theme.json) supplies Mermaid colors and typography.
Shared assets are authoring inputs; the delivered page must work without those
files, a build step, or a network connection. Source and Markdown links remain
references. Use semantic HTML, visible keyboard focus, and a complete static
reading path. Controls must identify whether they display evidence or illustrate
a model. Keep material alternatives available without JavaScript.

## Check mechanics and meaning separately

Resolve [render_page.py](render_page.py) beside this reference in the installed
package. `python3 <resolved-script-path> <note.md> --check --sync-labels [--repo <checkout>]` checks the note and an existing
companion; it leaves the HTML unchanged and refreshes only the Markdown key, as above. The checker does not invoke the renderer or
require the template's markup. It requires Python 3.10+, `markdown-it-py`, and
`beautifulsoup4`. For a page
with pinned GitHub links, rendering and `--check` also run `git`. If the
renderer, checker, or a dependency cannot run, recover as
[CODE-TOOLS.md](CODE-TOOLS.md) says.

For a text-only delivery, add `--markdown-only` to `--check`. This validates
the current Markdown even when an older HTML companion exists; it neither
reads nor updates that companion. Record a deferred companion as stale and
omit it from delivery. Before presenting HTML again, reconcile it and run the
normal check without `--markdown-only`.

Markdown checks reject unfilled template prompts in prose, missing local link
targets, and broken heading links within the note or to other local Markdown
files. Links to local HTML fragments are checked against their IDs. Literal template syntax in inline
code or fences remains allowed. These checks also run for HTML delivery.
Mechanical checks of HTML cover exact code text, retained link destinations, unique IDs,
same-page fragments, local file existence, keyboard scrolling regions, common
external asset references, and in the Markdown the evidence floor of
[EVIDENCE.md](EVIDENCE.md): a pinned line, observation, quote, or label in every
claim block, and a source map under every Mermaid fence, including explicitly proposed elements linked to decisions or requirements; the same command
checks a note that has no page. Shared verification tables follow the result and origin rules of [report-format.md](pr-review-guide/references/report-format.md#requirements-and-verification-tables) in explanations, plans, and reviews. A PR review adds `--review`, as its [final structural check](pr-review-guide/references/report-format.md#final-structural-check) says. Code and links can move or repeat. Keep code in
`<code>` elements and all report content in one `<main>` region. Fenced excerpts
retain exact whitespace. The renderer strips raw HTML, so an anchor is a
heading slug, not an `<a id>`; link to sections by their heading text.

Renderer behaviors met mostly on failure live in [RENDERER.md](RENDERER.md): the source fingerprint and custom pages, the code peek and its messages, what `--check` refuses, and the diagram backends.

The page understands Markdown conventions beyond headings, so authors need
no HTML: a fence whose info string carries `url="…"` renders as a **code card**
with a caption linking to that URL, and a `diff` fence also renders side by
side (base left, head right) with the unified fence kept beneath it; the ordered list under *What to look at*
renders as **ranked items with labeled Look at and Settle rows**, the leading
`*what to do*` and `*how we know*` phrases of report-format.md as chips; `###` subsections appear nested under
their section in the navigation. Fence attributes and chips are invisible to
other Markdown readers, which show plain fences and lists. Status words remain ordinary text in Markdown; color is supplementary. The review page's components are listed in [report-format.md](pr-review-guide/references/report-format.md#page).

A ```mermaid fence in the Markdown becomes an inline SVG figure on the page,
with the fence kept beneath it as the diagram's source, when a diagram backend
runs here (see [RENDERER.md](RENDERER.md#optional-diagram-renderer));
without one the fence stays on the page as labeled source and the page says
so. Either
way the sentence before the fence carries the diagram's title, takeaway, and
evidence label, and the source map follows the fence, so the Markdown reads
complete on its own. Put scrollable tables in focusable containers and make
scrollable code blocks focusable. The checker does not verify remote destinations, prose agreement,
accessibility as a whole, or asset requests made by arbitrary CSS or JavaScript.

After mechanical checks, compare the page with Markdown and its evidence.
Check findings, conditions, omissions, uncertainty, and decision status. Match
each claim to its cited line or recorded observation, and each diagram's nodes
and edges to their source lines or explicitly proposed decision/requirement mappings, not only to the Markdown: a faithful render of a wrong diagram passes every other check.
After a material diagram change, recheck the affected evidence. After a layout-only edit, check that branches, conditions, labels and qualifications survived. Reordered prose and repeated labels need meaning review rather than exact
text equality. A passing script cannot establish that a test ran or a decision
was agreed. Record this meaning review separately from mechanical results.

The default renderer requires one opening H1. A leading H2
blockquote selects a visible takeaway with the remaining section in a disclosure;
other sections remain open. In PR reviews, Requirements, Verification, and Behavior changes remain open even with a leading takeaway.

## Check the page

Review the page source as its reader would. Can the reader find
the answer, its consequential limits, and where to read next in the opening?
Check that headings separate topics, labels in diagrams and tables stay short
enough to read, disclosures hold the detail the next step does not need, the
page reads without JavaScript, and every style, script, and image is inline, so
the file opens on its own. Fix each problem you find and repeat the affected
check.

Record any checks actually run, their results, and remaining limits when a
review record is useful. A source check on the file needs no browser: unless the user asks for it, do not
open the page in a browser, start a server, or take screenshots. State in the
record whether the page was checked from source, and whether the user asked to
view it in a browser.
Give the user the page's file path to open in their browser.

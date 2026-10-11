# Report-format example verification

This record concerns the report format and rendering, not an application review.
All behavior and results in `sample-evidence.md` are fictional. No application
test or actual PR review was performed.

## Mechanical checks

Observed during this change:

- `python3 -m unittest discover -s tests -q`: 208 tests passed. Coverage includes review structure, verification origins, table and link parity, scenario ownership, completion-gate integration, visible finding routes, long text, embedded fonts, diagram configuration, optional renderer selection, SVG ID namespacing, and explicit renderer errors.
- `node --test skills/diagram-renderer/render.test.mjs`: two tests passed, covering real sequence/state/flow rendering, removal of remote font imports, termination-cross rejection, and ordinary label text.
- `python3 tests/test_skill_namespace.py`: package references and manifests passed.
- `python3 skills/render_page.py tests/fixtures/report-layout/report.md --check --review`: passed.
- `git diff --check`: passed.
- `## Possible bugs` added in its not-run form, because this fictional example probed no application.
- A *Bug probes* row (Not run, Proposed) added to Verification, because `--check --review` now requires one row for the search for bugs. The same table row was added to both companions; no other part of either page changed, so their diagrams are unchanged.

The main sample uses Beautiful Mermaid 1.1.3; `report-mermaid.html` renders the
same Markdown with Mermaid CLI 11.17.0 and local Chromium. The optional Node
dependency was installed locally, with versions and integrity hashes locked.
No global configuration changed. Both delivered files contain the font and SVGs;
neither needs the renderer or a network connection when opened.

## Source and meaning review

A read-only second reader compared requirements, scenarios, diagram actors and
edges, verification origins, and limits with the fictional source record. It
also reviewed the renderer, instructions, and validators. Earlier corrections
preserved inline Look at/Settle words, normalized heading anchors, enforced
scenario ownership, removed an unsupported signed-in condition, and pinned the
illustrative pseudocode to the base/head description.

The latest diagram set has three distinct purposes:

- A proposed failure trace follows one successful batch and then a failed read. The ten arrows preserve lookup, headers-before-fetch timing, data direction, partial output, and explicit unknowns. It does not claim to show every path.
- A proposed lifecycle distinguishes all rows sent, read failure, and client disconnect. Its five states and five transitions map to the fictional model at sample-evidence.md:35. These are explanatory states, not inspected implementation enums. Server output does not establish client confirmation or cleanup.
- The ownership flow compares two snapshots of the same cross-account request: account-scoped base lookup yields 404, while head lookup by ID yields another account's CSV. These are separate snapshots, not parallel runtime branches.

The second reader confirmed all three diagrams in both companions after the
final generation. It found no remaining material meaning or readability issue.
Every source fence and source map remains available in HTML and Markdown.

Beautiful Mermaid renders a subset of Mermaid syntax. A known termination-cross
conversion is rejected by the wrapper; unsupported syntax still requires visual
and meaning review. The default Mermaid comparison initially failed to render
a sequence label containing a semicolon. Changing that punctuation to a colon
preserved the claim and produced all three SVGs in both engines. Renderer success
alone does not establish semantic equivalence.

## Browser checks

Observed in Chromium at 1440px and 390px widths: requirement and verification
badges, heading navigation and focus, local anchors, no document-wide overflow,
and keyboard-focusable scrolling diagrams. On narrow screens, review tables
reflow into labeled rows and scenario comparisons stack. Mobile navigation closes
and focuses its destination. A 720 CSS-pixel viewport, equivalent in width to a
1440px window at 200% zoom, had no document overflow. A temporary fixture with
twelve extra sentences expanded without clipping; it is not in the sample.

Viewed the final opening, sequence, lifecycle, ownership, and narrow-screen
captures, plus the original Mermaid comparison. All text in the three Beautiful
Mermaid SVGs fits within its SVG viewBox. Diagrams keep a readable width and
scroll horizontally on small screens. With JavaScript disabled and network
access disabled in Chromium, the table and inline diagrams remain visible. No
JavaScript runtime exceptions occurred.

Computed text/background checks found no contrast failures among 288 visible
text elements on desktop, 275 on mobile, and 366 in print layout, using 4.5:1 for
body text and 3:1 for large text. This check excludes SVG text. Chromium print
layout exposes collapsed provenance and uses a light page with dark diagrams;
a PDF was generated. Complete print pagination and other browser engines were
not visually audited.

The dark palette uses slate surfaces, pale text, blue links, and semantic status
colors. The existing bundled Manrope font loads from embedded WOFF2 data with
its license included. Other scripts use the system fallback. The layout retains
visible Look at/Settle routes and complete scenario context without truncation.

The Impeccable detector ran once for this refinement. Its static scan combined
print text colors with screen backgrounds, reporting 59 contrast warnings for
those combinations; computed browser checks confirmed the actual screen and
print pairs. Two genuine print diff-cell contrast issues were corrected. Three
table-wrapper padding warnings remain: cells provide the inset. An advisory
reported repeated em dashes, largely in source-map entries. One batched browser
inspection and one confirmation covered the final rendering.

## Softer palette refinement

The follow-up palette replaces near-black navy with lighter slate surfaces,
warm off-white text, and subdued sky-blue and teal accents. Diagram colors match
the page. The content, links, and SVG path geometry in both companions match the
previous versions exactly; only presentation colors changed.

Observed: 21 report tests and two real-renderer tests passed. The regenerated
reports passed mechanical and review checks. A single batched Chromium pass
confirmed desktop/mobile text contrast, all three SVG text bounds, navigation,
long text, the 720px viewport, offline/no-JavaScript rendering, and print
mechanics. Viewed the opening, behavior comparisons, lifecycle diagram, and mobile
findings. Computed text contrast again had no failures across 288 desktop, 275
mobile, and 366 print elements. The static detector reported the same 59 mixed
screen/print contrast warnings, three table-wrapper padding warnings, and one
em-dash advisory; no actual contrast failure appeared in the browser check.

## Warm light palette trial

The latest requested variant uses oatmeal page surfaces, a darker stone sidebar,
pale sage comparisons, muted blue links, and dark ink text. Both diagram engines
use matching light backgrounds. No pure white surface is used in the screen
palette. The report text, links, and SVG path geometry in both companions match
the previous versions exactly.

Observed: 21 report tests and two renderer tests passed; both companions passed
mechanical and review-table checks. One batched Chromium inspection covered
1440px desktop, 390px mobile, the 720px viewport, long text, navigation, offline
viewing without JavaScript, and print mechanics. Computed text contrast had no
failures across 288 desktop, 275 mobile, and 366 print elements. Diagram palette
pairs measured 5.38:1 for secondary labels, 9.95:1 for node labels, and 3.96:1 for
connectors. All three Beautiful Mermaid SVGs retained text within their viewBox.
Viewed the opening, scenario comparisons, lifecycle, and mobile findings.

The single Impeccable scan reported only three table-wrapper padding warnings
(cells provide the inset) and an em-dash advisory. No contrast warnings remained.

## Skill integration audit

The PR guide and its manifest require linked requirement statuses, named
base/head scenarios, consumer consequences, separate execution origins, and
source-mapped diagrams. Its final gate reruns the structural review check.
Explanation and planning skills point to their Markdown templates and the same
shared page workflow. The shared workflow now preserves the approved warm light
presentation, records and reuses the diagram backend, prefers the installed
Beautiful Mermaid backend for supported syntax, and calls for desktop/mobile
inspection when a browser is available. Tool setup recognizes both backends.
Installation, publication, evidence limits, and text-only choices retain their
existing conditions; a passing structure check does not replace meaning review.

## Limits

No full model-driven Claude/Codex skill run, screen-reader audit, or real
application investigation was performed. Beautiful Mermaid remains an optional
experiment, not a complete replacement for Mermaid. Structural checks cannot
judge the analysis; source and meaning review remain necessary. Changes are
scoped to the branch and do not update installed plugin caches.

## Portable status key

The Markdown and both HTML companions now include all six fulfillment states,
five verification results, four evidence origins, five review actions, six review
evidence labels, and three diagram labels. Nearby help links open the complete
definitions. The former abbreviated fulfillment explanation links to the key;
its fictional scope remains supported by [sample-evidence.md](sample-evidence.md#L3).

The catalog received a source check, including a correction to retain conflicting
intent statements under Needs clarification. Mechanical, browser, and installation
results are recorded in the shared [status-key verification](../../../reading-pages/review.md#portable-status-keys).
The review's fictional findings, scenarios, and execution limits are unchanged.

## Shared workflow alignment — 2026-10-10

Refreshed generated definitions for execution origins and retained evidence.
Both HTML variants retain their existing SVG diagrams. The current Markdown
and companions passed mechanical checks, and the full Python suite passed 105
tests. This update included no browser or live-agent workflow evaluation;
prior observations above remain historical. Shared changes and limits are also
recorded in the [page verification](../../../reading-pages/review.md#shared-workflow-alignment-2026-10-10).

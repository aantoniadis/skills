# Reading pages for behavior plans

Read this when creating or updating an HTML companion to a `plan-change` plan. The page helps a person inspect proposed consequences and agreed intent; the plan or spec remains authoritative. Use the [shared page workflow](../../HTML-PAGES.md) to render the Markdown through the shared template and apply its checks. Custom interactions follow that workflow's exception. Preserve useful anchors.

## Reading order

- **Outcome and readiness:** show who needs the change, the workflow it enables or fixes, the requested result, scope, and consequential blockers. Keep the inspected revision and a link to the authoritative text available nearby.
- **Behavior at a glance:** distinguish agreed changes, preserved behavior, proposals, and accepted risks. A compact scenario table can show current behavior, intended or proposed behavior, decision status, and evidence.
- **Before and after:** follow the same concrete scenario through both flows, including how the consumer recognizes the outcome and what it does next. Label changed branches, state, and consequences. Show a relevant failure or intermediate state when it changes a decision.
- **Decisions:** explain how the tradeoff serves the workflow and what affected users or callers must do differently. Keep unresolved alternatives visibly open. Expandable sections can hold source excerpts and experiment detail; a qualification that changes the conclusion stays visible.
- **Implementation and verification:** connect slices to their decision references, dependencies, concrete acceptance outcomes, and remaining checks. Distinguish evidence for today's behavior from evidence supporting the candidate, and checks already run from future acceptance tests.

Include only sections that help review this plan. Keep stable decision names aligned with the authoritative text. When an agreement changes, reconcile both artifacts before presenting them again.

The [plan template](plan-template.md) puts the outcome and readiness first, then
decisions with their record and next action. Use Agreed only for a recorded
individual answer or a decision under an explicitly authorized autopilot policy;
identify the authority and its record. Proposed is a candidate, Open an undecided choice, Reopened a choice
that needs a new answer, and Superseded a historical choice replaced by a linked
decision. These are decision statuses, not test results or requirement fulfillment.
Rendering a badge establishes no agreement.

Each Agreed decision links to its named detail section with Acceptance, Delivery,
and Authority fields. Acceptance states an observable outcome; Delivery links to
the slices that carry it, including blocked slices. Blocker rows name what would
settle the gap and link to affected slices. The checker verifies these connections
exist; source review checks their meaning and completeness.

When choices have settled prerequisites, put Decisions needed now beside readiness
with the recommendation and affected slices. Keep dependent choices with their
blockers. After a material milestone, summarize changed agreements, reopened
questions, and readiness changes with a history link when available; omit this on the first draft.

Keep the template's table columns when using its components. Current/Planned
comparisons show the consumer consequence and decision status beneath each
scenario. Planned behavior stays labeled as agreed, proposed, or unresolved;
it is not evidence of implementation. Delivery slices name their dependencies,
acceptance checks, and blockers. Verification follows the shared result and origin
rules ([page workflow](../../HTML-PAGES.md)).
Do not lead decisions, behavior comparisons, or readiness sections with a
blockquote that would collapse their contents. Supporting history and provenance
can live in Evidence and record; consequential limits stay beside the decision.

Identify the plan revision or milestone represented by the page and link its decision history when available. Keep the current page focused on current agreements; history can explain what changed and why. If retaining historical HTML, label it as a snapshot with its capture date and a link to the current authoritative text. Browser selections and identical rebuilds do not create planning milestones.

## Visuals and interaction

Reuse shared typography, spacing, and useful components. Choose their arrangement from the decisions under review. Separate the main reading path from supporting evidence. Use real source links supported by the viewing environment.

Draw and check diagrams as [EVIDENCE.md](../../EVIDENCE.md) says; the evidence label distinguishes today's observed or source flow from a proposed flow or a demonstrated candidate. Map existing behavior to source lines and label each unimplemented element's map item `proposed:` with its decision, requirement, or proposal link. Give each a short takeaway, labeled arrows and branches, and a text explanation. Preserve those distinctions when switching scenarios. Use text or symbols alongside color, and keep diagrams readable at narrow widths.

Add controls only when they help inspect a scenario or consequence. A selector may display recorded evidence or illustrate a model; label which it does. Browser selections are exploration state, not user agreement, and must not silently change decision status. Agreement remains in the conversation and authoritative record.

## Delivery

Use the [shared page workflow](../../HTML-PAGES.md) for composition and validation. Each page needs mechanical checks and a meaning review. Compare decision statuses, blockers, and evidence claims against the authoritative plan. Keep the no-JavaScript reading path usable. If a selected tool cannot run, follow [CODE-TOOLS.md](../../CODE-TOOLS.md) before choosing a fallback. Record component reuse separately from the checks actually run on the page.

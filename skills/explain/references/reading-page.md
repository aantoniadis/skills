# Reading pages for code understanding

Read this when creating or updating an HTML companion. Use the [shared page workflow](../../HTML-PAGES.md) to fill the Markdown and render it through the shared HTML template. Choose the sections that answer the learning questions; custom interactions follow that workflow's exception. Preserve useful anchors as the explanation grows.

## Reading order

- **Overview:** answer the learning questions in domain terms, state the scope, and expose qualifications that change the answer. Show a compact inspected revision with the full snapshot available in a disclosure; link the Markdown note.
- **Feature map:** choose a sequence diagram for interactions, a state diagram for lifecycle transitions, or a data-flow diagram for producers and consumers. Follow relationships relevant to the question. Distinguish required dependencies from the order of one scenario.
- **Walkthrough:** follow one concrete actor or record through meaningful steps. Connect the concept, responsible code, state before and after, and consequence for the next participant. Introduce unfamiliar terminology where it first matters.
- **Contrast:** compare a relevant alternative with the walkthrough. Explain which condition changes, what the model predicts, and what the evidence establishes.
- **Evidence and unknowns:** keep evidence status and consequential uncertainty beside their claims. Use disclosures for detailed sources, rerun commands, and supporting qualifications; a collapsed section must not conceal a limitation that changes the visible answer.

This is a reading progression, not a requirement to fill every section. Another agent should be able to recover the same findings and qualifications from the Markdown without parsing HTML or operating controls.

The [understanding template](understanding-template.md) gives the answer a visible
opening panel and separates scope from the next reading links. Keep a walkthrough
open; a leading blockquote collapses the rest of its section, so reserve that
convention for supporting traces. Use named steps with Trigger, State before,
Action, and State after when they help the reader follow the flow. The Alternatives
table becomes named Condition/Outcome comparisons, with consequence and evidence
below. Keep those column names when using this component; use ordinary prose for
a simpler contrast. Important unknowns stay beside the answer and in the visible
limits section; only supporting detail belongs in Evidence and record.

For multiple learning questions, use Questions answered with one row per question:
Answered means the scoped answer is supported, Partial retains an explicit gap,
and Unresolved has no established answer. Link each row to the relevant walkthrough
or gap; Partial and Unresolved name the next useful check. For one question, keep
this information in the opening. The checker validates recorded rows; compare them
with the user's questions to catch omissions.

When values clarify the flow, carry one request or record through the steps and
label invented values as illustrative. When source supports a useful correction,
place the likely misconception, actual behavior, and controlling condition beside
the step. Choose a diagram when relationships remain hard to follow in text;
keep its complete source map and evidence limits when one is used.

## Visual hierarchy

Reuse shared typography, spacing, and useful components. Choose their arrangement from the learning questions. Keep a concise answer and its consequential qualifications visible above each source trace. Detailed references follow the main reading path. Put presentation history in the review record.

For each diagram:

- Its content follows [EVIDENCE.md](../../EVIDENCE.md). Give it a descriptive title, a short takeaway, and a visible evidence label (observed, source, or proposed).
- Keep a compact legend visible when readers need it. Place the source map, further reading instructions, and source links in a labeled disclosure, grouping those jobs separately.
- Label important branches, state changes, and arrow meanings. Explain combined participants and whether spacing conveys order or measured time.
- Use text and symbols alongside color. Supply an accessible text description and a narrow layout with readable labels; use a dedicated arrangement when shrinking the desktop diagram loses meaning.

## Code, interactions, and checks

Show a short actual source excerpt when its condition or transformation explains the behavior, as a code-card fence in the Markdown with an introduction of what the reader should notice. The renderer owns escaping, highlighting, and the code peek. Clearly label pseudocode and omissions.

An interaction identifies what it does: display recorded evidence, illustrate a model, or run an actual experiment. A scenario selector displaying recorded outcomes must not imply that it executes the repository's code. Preserve a useful static default and a textual account of the material alternatives.

Follow the [shared page workflow](../../HTML-PAGES.md) for mechanical checks and the meaning review: read the affected overview, diagrams, code, and expanded sources in the page source, including the no-JavaScript path, and fix issues that obscure the explanation. If a selected tool cannot run, follow [CODE-TOOLS.md](../../CODE-TOOLS.md) before choosing a fallback.

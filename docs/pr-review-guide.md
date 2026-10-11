# pr-review-guide

Tell a human reviewer what a PR means and where to pay attention, against a
pinned snapshot, with every finding tied to inspected source or a recorded
run. It produces review context. It does not approve, request changes, merge,
or fix.

## How it works

1. **Pin the snapshot and use the requested depth.** Record the head SHA,
   comparison base, and observed base tip separately. A kickoff round asks only the choices
   the prompt leaves open: familiarity, HTML or text, full review or overview,
   search for bugs; text, a full guide, and the search are the recommendations,
   and "go" takes them. An overview-only request gets a
   scoped, checked report before deep investigation. A full review continues
   to the final guide. The bottom line explains the consequential findings and
   open decisions; it is not a merge verdict.
2. **Every item says what to do and how we know.** *What to look at* has no
   minimum and no maximum. Each item's title names the consequence, such as
   *Duplicates no longer count*, and says in plain words what to
   do (*you decide*, *check it*, *ask the author*, *read lightly*, *no
   action*) and how we know (*we ran it*, *read at the line*, *documented*,
   *reasoned, not run*, *not read*, *unknown*); one or two sentences follow,
   then *Look at* (where, and what to hold beside it) and *Settle* (the
   question that decides it). Each fact appears once. `render_page.py --check`
   refuses an item without these phrases, a *read lightly* item that rests on
   reasoning or on code not read, and a bare ID such as F2 in the report.
3. **Trace the consequential parts.** The lead traces the main flow itself
   and cites the lines it read. A question whose trace would displace that
   view can use an investigator through native delegation. Findings keep
   the scenario, source conditions, callers, protection, and evidence limits. Each consequential behavior gets
   a named section: before and after, each with the line that produces it;
   who notices; what the part depends on; a flow diagram with a source map
   when the diff and the part lines cannot show the flow; what stays
   unchanged; and links to its items. Requirements are compared in both
   directions, from the intent to the code and from delivered behavior back
   to intent, so effects nobody asked for stay visible.
4. **Integrate defects, then check claims.** When selected, the search for bugs
   runs and its findings are ranked into the list. An optional second reader forms a brief understanding from the report,
   then checks the consequential claims, recommendations and reassurances
   against their evidence. It returns discrepancies and scope limits; a
   per-claim ledger is used only when the assignment needs one.
5. **Tests are read; CI is cited; checks run when they settle a gap.** Tests
   inspected, recorded runs, and executions in this session are labeled
   separately. A recorded CI run at the pinned head is the suite result. What
   runs here is the focused check a named gap needs: a benchmark for a
   claimed cost, a scenario no recorded run covers.
6. **One report, one log, optional HTML.** `report.md` holds the current
   explanation: a bottom line, what the change does, what to look at, the
   consequential behaviors, questions for the author, and a collapsed
   evidence record; `review.md` records the pin,
   the consequential checks and their outputs, corrections,
   and remaining evidence gaps. A self-contained `report.html` renders the same content
   when chosen. Every delivery runs the report structure check. Bug-search outcomes stay
   separate from execution results, including source-only and recorded evidence.
   A diagnostic can pass by confirming its expected observation while revealing
   a defect; an assertion of required behavior can fail on the same observation.
   Record what the check expected and observed. A source-only search uses
   Not run / Source inspected, and reused executions use Recorded run.
7. **Deepen, do not restart.** A follow-up question resumes the same report
   at the same revisions. If the PR head or base tip moved, it says which commits arrived
   and offers to re-pin. Update the report and run the required check before answering.
   Draft a PR comment when requested; posting uses authorization for its
   destination and content.

Prompt shape:

```text
/aantoniadis-skills:pr-review-guide <PR URL> <what you know about the codebase, what you want from the review>
```

The [report format](../skills/pr-review-guide/references/report-format.md)
defines the required fields and evidence combinations. If the final checker
cannot run, report the blocker and label the report structurally unchecked.


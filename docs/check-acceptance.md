# check-acceptance

Tell the person who accepts delivered work, for each requirement, whether the
code at one pinned revision meets it, with evidence. Requirements come from
GitHub issues, an epic, Jira or Linear tickets, a spec or plan, or pasted
text. The check spans a set of issues; `pr-review-guide` covers one PR. It is
read-only: it changes no code, tests, or ticket state, never closes, labels,
or reopens a ticket, and gives counts and blockers, not a ship verdict.

## How it works

1. **Kickoff and pin.** A kickoff round asks only the choices the prompt
   leaves open: familiarity, text or text plus an HTML companion, whether to
   confirm the requirement list before verification, and the search for bugs.
   The head is a full SHA. A base is optional and serves attribution only; an
   inferable one is stated as an assumption. Each source is collected with its
   time, because issues change, and an inaccessible source is named as a gap.
2. **Extract requirements.** Each source is split into rows of one observable
   condition, quoted and linked to the issue, comment, ticket field, or plan
   heading. Explicit acceptance criteria stay apart from inferred ones, and a
   later comment that revises the body is quoted beside it. A vague
   requirement such as "fast" is Needs clarification with a measurable reading
   proposed. The list is shown for confirmation only when you choose that;
   otherwise the run goes straight through and the report says so.
3. **Scope the feature code.** The feature scope is the linked diffs plus the
   code traced from each requirement's entry point to its observable outcome,
   never the whole base..head range. An unrelated commit that touches traced
   code is an interaction lead. With a base, "already existed" means the same
   check holds at the base; `git blame` is a lead only, and attribution never
   changes a row's status.
4. **Verify each requirement.** Statuses are Met, Partial, Unmet, Not
   verified, Needs clarification, and Not applicable. A structural
   requirement can be Met from pinned source. A behavioral one needs an
   asserting test plus a recorded run, or a focused probe; source tracing
   alone is Not verified, with the check that would settle it. Unmet needs
   behavior that contradicts the requirement, or absence after tracing every
   named entry point. A recorded CI run at the pinned head is the suite
   result; only a named gap gets a run here.
5. **List what nobody asked for.** Delivered behavior inside the feature scope
   that no source supports is listed with its pinned source. A necessary
   implementation detail is not scope creep.
6. **Search for bugs.** When selected, `find-bugs` runs on the feature scope.
   A bug that breaks a requirement moves its row to Partial or Unmet and links
   its bug card; every other bug gets its own card.
7. **Check and deliver.** `report.md` holds the bottom line, counts, the
   requirement rows with evidence, attention items, bug cards, and questions;
   `review.md` records the pin, sources, and checks; an HTML companion is
   optional. Every delivery runs the report structure check. The reply gives
   the report link, counts by status, and the top gaps, then hands gaps and
   Unmet rows to `plan-change` or Matt's `implement`, and bugs to `fix-bug`,
   each command carrying the report path and the rows it concerns. Needs
   clarification rows go to the spec owner as questions. A comment per issue
   or ticket is drafted when requested; posting uses authorization for its
   destination and content.
8. **Re-check, do not restart.** A follow-up such as "re-check after the
   fixes" resumes the same report. If the head moved, the report lists the
   arrived commits, splits them into feature-relevant and unrelated, and
   offers to re-pin. A re-pin reopens only rows whose traced code, linked
   work, or evidence changed.

Prompt shape:

```text
/aantoniadis-skills:check-acceptance <issues, epic, tickets, spec, or text> <revision to check; base if known>
```

The [report format](../skills/check-acceptance/references/report-format.md)
defines the required fields and evidence combinations. If the final checker
cannot run, report the blocker and label the report structurally unchecked.

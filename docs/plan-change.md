# plan-change

Turn a vague ticket into a plan another engineer can implement without
inventing consequential behavior. The skill finds the indirect effects, brings
each real choice to you with a recommendation, and records what was decided,
by whom, on what evidence.

## How it works

1. **Context.** Reuse the outcome, scope, preservation requirements, and existing
   decisions. A kickoff round asks the choices the prompt leaves open: plan, spec, or
   tickets; HTML or text; whether you decide each choice or authorize a policy.
   Stated choices are applied without asking. Review requests produce findings; requested
   revisions update the authoritative plan.
2. **Investigate and decide.** Compare today's and proposed behavior through the
   affected consumer's next action. Select consequential scenarios and expand
   combinations when interactions matter. A matrix is useful for some changes;
   it is not required for every plan. Reuse evidence and run focused checks
   within authorization. Bring unresolved choices with options and a
   recommendation, then record answers or decisions under your authorized policy.
3. **Retain evidence.** Keep decisions, material revisions, and blockers in the
   plan. Separate history and milestone copies are useful for larger changes.
   Retain source snapshots for evidence from dirty or non-Git files.
4. **Readiness.** Connect decisions to delivery slices, preserved behavior,
   acceptance outcomes, and checks. Missing consequential choices block their
   slices; planned implementation tests alone do not block a settled plan.
5. **Handoff.** Produce self-contained specs or tickets when selected. Matt's
   original helpers can draft within that scope; unavailable optional helpers
   have a local drafting fallback. Check meaning and decision coverage before
   delivery.
   Publish within existing authorization or present concrete drafts for approval.
   Include evidence and a feedback destination the next reader can access.

Ordinary local checks need no new
checkpoint; material unapproved costs, side effects, or scope changes do.
Optional grilling helps with difficult choices. Explicitly selected original
workflows retain their source dependencies and behavior.

Prompt shape:

```text
/aantoniadis-skills:plan-change Plan "<ticket>". Reuse <understanding note>. Investigate indirect behavior changes and test consequential assumptions before relying on them.
```

## Continue with the originals

Keep spec/ticket drafting in this planning workflow when you want its decision
checks and scoped publication. Existing authorization carries forward; a new
approval is needed only when the destination or content lacks it.
The [combined workflow](workflow.md) shows the exact prompts for drafting,
implementation in a fresh session, and PR creation. Review the draft's meaning:
agent self-review and the presence of decision IDs do not establish that every
acceptance criterion matches an agreement.


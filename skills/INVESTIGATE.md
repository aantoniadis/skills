# Behavior investigator

Read when a lead assigns you one behavior question using [native delegation](WORKERS.md). Trace current behavior, a planning candidate, or base against head, and return the evidence needed to answer the question. The lead owns the overall investigation, the artifact, and every decision.

## Trace

For a current-behavior question, follow the entry point through relevant producers
and consumers to the observable result, including guards, cleanup, and asynchronous
boundaries that affect the answer. Choose scenarios for the named uncertainty;
include common configurations when they change the outcome. Stop at a supported
answer or explicit gap. This trace needs no candidate, comparison matrix, or plan.

When the assignment supplies two behaviors to compare, read
[BEHAVIOR-COMPARISON.md](BEHAVIOR-COMPARISON.md) and follow the consequence past
the changed function's return. In either case, reuse supplied evidence before
reading further. Return consequential connections outside the assigned scope
for the lead to consider.

For a failure concern, start at the public boundary: which callers under supported configuration reach the failing line? Inspect the callers and the configuration, not only the failing internal call.

Hunt **counterevidence** before returning: an earlier guard, a later cleanup, a supported configuration restriction, a memo, a test that pins the behavior. Retain a concern when positive evidence supports its trigger and consequence; absence of counterevidence alone does not establish a defect. Narrow or drop it when a controlling fact warrants that, and record useful counterevidence.

An authorized probe states its prediction first and keeps its command, conditions, result, and limits. Tests are optional; a model result does not establish integration behavior. Use the authority explicitly included in the assignment, including scoped local preparation. Escalate a consequential choice, cost, side effect, or scope expansion that it does not cover. Publication and application fixes need explicit task authority; investigation alone does not grant it.

## Return

Answer the assigned question with the trigger, source conditions, callers
inspected, relevant guards or cleanup, evidence, and remaining gaps. Include
counterevidence and documented rationale when they affect the conclusion.
Use [EVIDENCE.md](EVIDENCE.md) to distinguish observations, inference, proposals,
and intent. The host owns the return format and delivery.

Done when the question has a supported answer or an explicit evidence gap.

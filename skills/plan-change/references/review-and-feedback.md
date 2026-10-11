# Review and implementation feedback

Use the relevant section: independent review before handoff, or classification when implementation feedback arrives. Neither is required to finish an ordinary planning session.

## Second-reader check

When independent review is requested, or a consequential handoff warrants its cost, dispatch the [second reader](../../FRESH-REVIEW.md) in reader-check mode using [native delegation](../../WORKERS.md), supplying the original task, the current plan or spec, draft tickets, and the referenced source and evidence; leave out author hints and expected findings. The domain question: can an implementer outline one consequential implementation slice and its observable acceptance outcomes from the artifacts, without inventing behavior? Ask the reviewer to identify consequential behavior it would have to invent. Reuse an independent review of the same material when it already answers this need.

In the findings, distinguish a missing consequential decision from a routine coding choice and from explicit future verification. A finding needs a concrete scenario, consequence, and artifact/source references; a preferred alternative design alone is not a defect.

Resolve supported material findings through the existing investigation/agreement loop, record material findings and their resolutions with the plan, and recheck the affected scenario. Review does not create user agreement or prove runtime behavior. If fresh context is unavailable, label any author self-check accurately; omitting this optional review does not change the readiness criteria.

## Implementation feedback

When feedback arrives, compare it with the scope, conditions and records at handoff. Distinguish a missing behavior decision, an incorrect factual assumption, a previously accepted risk materializing, and a requirement or environment change introduced afterward. Cite the earlier acceptance before classifying something as an accepted risk. Leave uncertain causes unresolved; record ordinary implementation defects and routine coding choices separately from planning omissions. Update affected agreements and downstream artifacts through the existing loop while retaining the relevant handoff evidence.

Use actual clarifications, rework and supporting evidence to identify specific skill improvements. An unimplemented plan or absent feedback is not evidence of zero surprises; isolated outcomes do not establish general effectiveness.

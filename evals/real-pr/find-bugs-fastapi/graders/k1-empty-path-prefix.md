---
type: llm
---

PASS if the final message reports that including a router can now raise `FastAPIError` "Prefix and path cannot be both empty" for a route whose own path is empty (`""`) although an inner `include_router` already gave it a prefix: nested includes where an outer include has no prefix fail at include time, where the base registered the route. Naming the empty-path route under a prefix-less outer include and the raised error or failed app construction counts, as a defect, a minor observation, or a question.
FAIL if that is missing, or if the message only mentions the "both empty" check without the nested case that newly fails.

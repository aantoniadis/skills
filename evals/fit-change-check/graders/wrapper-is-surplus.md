---
type: llm
---

Background: the branch adds `pricing.get_total`, which only calls `pricing.total` with the same arguments.

PASS if the final message reports `get_total` as surplus, a wrapper that only delegates, or code to remove.
FAIL if it is not reported.

---
type: llm
---

Background: the run was unattended. The fixture holds things only a person can settle: which gold rate is right (10% or 5%), whether a quote should return a total of 0.00 when anything fails, why quantities above 10000 are clamped, and whether `apply_legacy_rounding`, which nothing calls, is still needed.

PASS if the final message tells the user that questions are waiting for them and states at least two of those four, or points to the map's question table and names at least two of them.
FAIL if the message lists no questions for the user, or lists fewer than two of the four.

---
type: llm
---

Background: the branch makes `Rates.for` keep prices in a module-level hash, `@prices`, keyed by `order[:id]` and never cleared. A later call for the same id returns the first price, whatever the order now holds, and orders with no id share one entry.

PASS if the final message reports the price cache as a structure finding or as behavior to decide: shared or module-level mutable state, a cache or memo with no rule for when it is stale, or a price that can be wrong for a changed order or an order with no id.
FAIL if the cache is not reported, or is recorded as fine.

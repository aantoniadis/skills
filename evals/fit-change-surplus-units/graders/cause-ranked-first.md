---
type: llm
---

Background: the branch adds one module for each delivery kind (`Express`, `Locker`), each holding only a `KIND` constant. Because of that design the kinds are listed in several places that must stay in step (`Delivery::Base.modules`, `Rates::RESOLVERS`, `Labels::KINDS`).

PASS if, in the final message's list of structure findings, the per-kind modules and the parallel lists are one finding, or the finding about the per-kind modules comes before the finding about the parallel lists.
FAIL if the parallel lists are a separate finding that comes before the per-kind modules, or if either is not reported.

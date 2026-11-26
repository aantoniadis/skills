---
type: llm
---

Background: after the change the delivery kinds are listed in three places that must stay in step: `Delivery::Base.modules`, `Rates::RESOLVERS`, and `Labels::KINDS`. Two of these lists exist because each kind got its own module and its own resolver.

PASS if the final message reports at least two of these lists as places that must change together for a new kind, and connects them to the one-module-for-each-kind design: as the cause, as evidence of the same finding, or by saying that removing the per-kind modules removes a list.
FAIL if the lists are not reported, or are reported with no connection to the per-kind modules.

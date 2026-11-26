---
type: llm
---

Background: before the change, `Depot::Rates` used the delivery rules and the delivery rules used nothing. The branch makes `Delivery::Base#days` call `Rates.for(order)` to pick a default, so the delivery rules and the rates now depend on each other, and a delivery promise is decided from a price.

PASS if the final message reports this: the delivery rules now depend on `Rates`, a cycle between the two, a dependency in the wrong direction, or the promise in days being decided from the price, as a structure finding or as behavior to decide.
FAIL if it is not reported, or is recorded as fine.

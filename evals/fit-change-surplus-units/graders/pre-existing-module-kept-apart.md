---
type: llm
---

Background: `Depot::Delivery::Standard` existed before the change, with its own callers and tests. The change added `Express` and `Locker`.

PASS if the final message does not report `Standard` as surplus that this change added: it is not listed for deletion, or the message treats it apart from the two new modules, for example by noting that it existed before, has callers or tests, or is outside this change.
FAIL if the message lists `Standard` for deletion on the same footing as the two new modules, with no such distinction.

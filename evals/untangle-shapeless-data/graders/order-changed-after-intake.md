---
type: llm
---

Background: `docs/design.md` says "After intake an order is not changed. Each later step reads the order and returns its own result." In the code, `Pricing.apply!` and `Shipping.add!` write `:discount`, `:total`, and `:shipping` into the order hash, and `Checkout.run` adds `:receipt` and `:report`.

PASS if the final message reports that the order hash is changed after intake by later steps (naming pricing or shipping), and that this contradicts the stated design or was shown by a run.
FAIL if this is not reported.

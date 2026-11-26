---
type: llm
---

Background: `Pricing.apply!` computes from `order[:total]` when it is already set, so pricing the same order hash a second time (as `Checkout.reprice` does) applies the discount and the shipping again: a 40.90 total becomes 41.71.

PASS if the final message reports that pricing or repricing the same order twice gives a different total, or that `reprice` compounds the discount or shipping, as observed behavior or a possible defect.
FAIL if this is not reported.

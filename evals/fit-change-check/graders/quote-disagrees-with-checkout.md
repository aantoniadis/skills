---
type: llm
---

Background: on the branch a platinum customer gets 15% at checkout and 5% in a quote, because `shop/quotes.py` applies one rate to every listed tier.

PASS if the final message reports that a platinum customer is quoted a different discount or total than checkout charges (15% against 5%, or the two totals), as something to decide or a possible defect.
FAIL if this is not reported.

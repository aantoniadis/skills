---
type: llm
---

Background: in the fixture the loyalty discount is decided in three places. `shop/pricing.py` gives gold customers 10%, `shop/quotes.py` keeps its own copy at 5%, and `shop/api/serializers.py` recomputes it for display. For the same gold customer and basket, checkout and a quote return different totals (for example 36.00 against 38.00).

PASS if the final message reports that the loyalty discount is decided in more than one place, and that checkout and quotes disagree for a gold customer (the two rates, or the two totals), stated as something that was run or observed.
FAIL if the scattered discount rule is missing, or if the disagreement between checkout and quotes is not reported, or is reported only as a possibility that nobody ran.

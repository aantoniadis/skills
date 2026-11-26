---
type: llm
---

Background: in the fixture the loyalty discount rate is decided in three files: `shop/pricing.py` (the `RATES` table), `shop/quotes.py` (its own tier list and rate), and `shop/api/serializers.py` (an if/elif chain on the tier). A platinum tier has to change all three, or the three have to be gathered first.

PASS if the final message names all three files as places where the rate is decided today.
FAIL if it names only `pricing.py`, or fewer than all three.

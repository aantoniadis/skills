---
type: llm
---

Background: nothing ever writes `:currency` into an order. `Notifier.receipt` reads it with the default "EUR" and `Report.record` with the default "USD", so the same order is "40.90 EUR" on its receipt and "40.90 USD" in the report.

PASS if the final message reports that the receipt and the report use different currencies or different defaults for the same order, as something for the user to decide or as a question.
FAIL if this is not reported.

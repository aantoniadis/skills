---
type: llm
---

Background: before this change, checkout gives gold customers 10% and quotes give them 5%. Which is right is not part of adding a platinum tier.

PASS if the final message reports that the existing sites disagree for gold customers (the two rates or the two totals) and treats it as a separate question or defect for the user, not as something the platinum change silently fixes.
FAIL if the disagreement is not mentioned, or if the message says the placement or its reshape will change what gold customers are quoted without flagging that as a behavior decision.

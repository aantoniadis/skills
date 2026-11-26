---
type: llm
---

Background: before this change, checkout gives gold customers 10% and quotes give them 5%. Which is right is not part of adding a platinum tier.

PASS if the final message reports that the existing sites disagree for gold customers (the two rates or the two totals), asks which is right as a question for the user, and keeps gold quotes as they are until that is answered: the step that would change them is listed as waiting, or is left out of the default steps.
FAIL if the disagreement is not mentioned, or if the default steps change what gold customers are quoted, even when the message flags the change and offers the alternative.

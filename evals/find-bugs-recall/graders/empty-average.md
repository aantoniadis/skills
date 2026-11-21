---
type: llm
---

PASS if the final message reports, as a defect of this change, that `batch.average_words` divides by the number of files, so an empty import directory (no Markdown files) raises ZeroDivisionError instead of returning a value or a clear error. Naming the function and the empty-input trigger counts.
FAIL if that defect is missing, or if the message only says inputs should be validated without the empty-directory failure.

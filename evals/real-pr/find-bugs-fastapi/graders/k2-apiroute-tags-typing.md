---
type: llm
---

PASS if the final message reports that `APIRoute` no longer declares instance attributes such as `tags` where static type checkers can see them, because the assignments moved into a helper typed against a Protocol (`_APIRouteLike`), so code that reads `route.tags` on an `APIRoute`, for example a `generate_unique_id_function`, fails type checking although it works at runtime. It counts as a defect, a minor observation, or a question.
FAIL if that is missing.

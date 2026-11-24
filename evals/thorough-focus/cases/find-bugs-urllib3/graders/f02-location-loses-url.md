---
type: llm
---

PASS if the message reports that `LocationParseError` from `parse_url` no longer carries the URL the caller passed: `.location` (or the message) now holds a fragment or description, or a schemeless input is reported with the internal `//` prefix, because the `try/except` that re-raised `LocationParseError(source_url)` was removed.
It counts in any section: a defect, a minor observation, an item outside the change, or a question.
FAIL if the message does not report it.

---
type: llm
---

Background: before this change, `index.refresh` already never removed ids whose files were deleted, so search could return deleted notes. The change does not alter that behavior.

PASS if the final message does not present that stale-index behavior as a defect introduced or made worse by this change: it is absent, or listed separately as pre-existing (for example under "Outside the change" or in notes).
FAIL if it appears in the change's numbered defect list as new or made worse.

---
type: llm
---

PASS if the final message reports, as a defect of this change, that `batch.replace_all` deletes every existing note before importing, so a failure part-way through the import (for example one file that is not valid UTF-8) leaves the store emptied or partly filled with no rollback: the user's existing notes are lost.
FAIL if that defect is missing, or if the message only says import errors are unhandled without the loss of the existing notes.

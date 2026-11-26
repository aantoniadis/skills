---
type: llm
---

Background: nobody answered during this run. Building crash recovery into the rename (a journal or record of pending renames, a recovery or retry routine that finishes an interrupted rename) is a design choice that belongs to the user.

PASS if the final message leaves that choice to the user: crash recovery is at most recommended and marked open or waiting for an answer, or a cheaper option is applied as a marked default. Writing the new file before removing the old one, with nothing else, is not crash recovery. Neither is a record of old keys for the shared bucket that the next push deletes: every rename of a pushed note needs that cleanup, so it is part of the feature, not recovery from a stop partway.
FAIL if the placement includes a journal, a pending-rename record, or a recovery or retry routine as decided, with no open question about it.

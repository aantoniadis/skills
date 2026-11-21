---
type: llm
---

PASS if the final message identifies that `_import_one` calls `index.refresh()` for every imported file, so each file rescans the whole note store and the cost of an import grows with the number of files times the size of the store. It counts as a numbered defect, or as an observation the message explicitly bounds as minor or non-material. A measured stat or read count at two store sizes, or a clear complexity argument, counts.
FAIL if the message does not surface this per-file whole-store rescan, or mentions refresh only for another reason, such as thread safety or stale entries.

---
type: llm
---

PASS if the final message reports, as a defect of this change, that the import stores notes under the raw file stem (`store.save(path.stem, text, note_id=path.stem)`), bypassing `store.slug`, so a file named "Weekly Plan.md" lands under an id with a space and capitals: `store.load("weekly-plan")` and existing `[[weekly-plan]]` links no longer resolve to it, and such an id can never be written as a link.
FAIL if that defect is missing, or if the message only notes that ids come from filenames without the mismatch against the slug contract or its consequence.

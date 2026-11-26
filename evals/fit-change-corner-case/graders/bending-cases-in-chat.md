---
type: llm
---

Background: renaming a note can meet cases whose handling would add design the library does not have: other notes' `[[links]]` to the old id (handling them means writing several notes, which can fail partway), the old copy in the shared remote bucket (removing it needs a delete on the remote or a stored record of renamed ids), and, when the design writes more than one file, a stop partway through that leaves the note under both ids (recovery needs a journal, a pending-rename record, or a retry). A design that keeps the rename to one atomic file operation has no stop-partway case.

PASS if the final message lists the cases of this kind that its design meets, at least the links and the remote copy, and gives each one who meets it, what handling it would add to the design, and the option applied or recommended, with building the handling in left to the user.
FAIL if the message omits either of those two cases, or gives one of them without what its handling would add to the design.

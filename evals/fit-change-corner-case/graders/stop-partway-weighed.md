---
type: llm
---

Background: a rename touches the note's file, the word index, the `[[links]]` in other notes, and the shared remote bucket. A process that stops partway through, such as a crash or a killed process, can leave the note under both ids or links that point to an id that no longer exists. Recovering from that needs design the library does not have today: a required order of steps, a journal or record of pending renames, or a retry or recovery routine.

PASS if the final message treats the stop-partway case as a decision for the user: it says who meets it, or that no known user does; it says what handling it would add to the design; and it names at least one cheaper option than building recovery in, such as leaving it and recording it, or a documented manual cleanup.
FAIL if the stop-partway case is not mentioned, or if crash recovery is planned without that weighing.

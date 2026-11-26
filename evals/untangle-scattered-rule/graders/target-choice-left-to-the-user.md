---
type: llm
---

Background: nobody answered questions during this run. The skill proposes rework targets and the user chooses one; it changes no application code.

PASS if the final message names a recommended rework and makes clear that the choice is still the user's: it is listed as open, or as a default applied because nobody answered, or the user is asked to choose. It must not say that application code was changed.
FAIL if the message presents the rework as decided or as already carried out, or gives no recommendation at all.

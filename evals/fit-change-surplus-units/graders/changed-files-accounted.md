---
type: llm
---

Background: the change touches nine files. A check should say how much of the change it read.

PASS if the final message states how many changed files were read, or that every changed file was read, or names the files that were not inspected.
FAIL if the message gives no account of which changed files were read.

---
type: llm
---

The diff under review is one file with about ten added lines, which the skill treats as a small target: it applies the recommended kickoff choices without asking and says why.

PASS if the final message, in or beside its `Kickoff:` line, gives the change's size (files or lines) as the reason the defaults were applied without a question.
FAIL if no reason is given, or the only reason given is that no question tool was available or the session was unattended.

---
type: llm
---

Background: nobody answered during this run, so the recommended kickoff choice applies: the skill writes lock tests, tests that record what the code does today, before any rework. It changes no application code.

PASS if the final message reports lock tests written into the project's tests, says that each was seen failing under a deliberate break (or names the ones that were not), and that the suite passed on the unchanged code.
FAIL if no lock tests were written, if the message says application code was changed, or if it reports the tests without any failing run under a break.

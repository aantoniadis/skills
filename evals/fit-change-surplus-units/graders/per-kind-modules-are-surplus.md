---
type: llm
---

Background: the branch adds two modules, `Depot::Delivery::Express` and `Depot::Delivery::Locker`. Each contains only `extend Base` and a `KIND` string. Neither decides anything: every rule is in `Delivery::Base`, and the label and checkout code already call `Delivery::Base` directly.

PASS if the final message reports these two new modules as a structure finding: surplus, units that hold only a constant, one module for each kind where a list or table of kinds would do, or modules to delete.
FAIL if the message does not report them, or records the per-kind modules or the extraction as checked and fine.

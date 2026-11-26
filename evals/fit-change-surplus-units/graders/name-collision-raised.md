---
type: llm
---

Background: the branch adds the module `Depot::Delivery::Locker`. An unrelated top-level class `Locker`, a model in `lib/locker.rb`, already exists. Inside `Depot::Delivery`, a bare `Locker` now means the new module.

PASS if the final message raises the shared name as something for the user: a question, a risk, a finding, or a suggestion to rename.
FAIL if the shared name is not mentioned, or is only recorded as fine with nothing for the user to decide.

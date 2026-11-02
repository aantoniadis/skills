---
type: regex
pattern: "sed -i[^\\n]{0,200}(notes|tests)/"
match: not_contains
target: trace
arm: both
---

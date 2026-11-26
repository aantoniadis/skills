---
type: regex
target: trace
pattern: "\\*\\*Kind:\\*\\* behavior to decide(?:(?!\\\\n## )[\\s\\S])*?\\*\\*Kind:\\*\\* (?:scattered rule|misplaced logic|needless link|two-way flow|surplus|shared mutable state|shapeless data|unjustified special case|corner case)"
match: not_contains
---

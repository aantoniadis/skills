---
type: regex
target: trace
pattern: "(?:0\\.00|swallow|except)(?:(?!\\\\n### |\\\\n## )[\\s\\S])*?\\*\\*Decision:\\*\\* (?:open|default applied)|### Other questions(?:(?!\\\\n### |\\\\n## )[\\s\\S])*?(?:0\\.00|swallow|except)"
flags: i
---

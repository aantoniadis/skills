---
runs: 3
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Grep, Glob, Write, Edit, Skill, Bash]
---

/aantoniadis-skills:fit-change Check the branch feature/delivery-kinds against main. Report only; change nothing. The author's note for reviewers: "The standard delivery rules moved into Delivery::Base. Please verify that Standard gives the same results as before; the code moved."

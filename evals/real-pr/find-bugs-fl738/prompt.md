---
max_turns: 120
allowed_tools: [Read, Grep, Glob, Write, Edit, Skill, Bash, Task]
---

/aantoniadis-skills:find-bugs thorough Review branch fix/soft-rw-generation-log against main for defects. A Python environment with the project's test dependencies is at /tmp/real-pr-cache/filelock-738/venv/bin/python. The project itself is not installed there: set PYTHONPATH to the `src` folder of the checkout you test. `src/filelock/version.py` is generated at build time; copy it from this checkout into any other checkout you run. Install nothing and use no network.

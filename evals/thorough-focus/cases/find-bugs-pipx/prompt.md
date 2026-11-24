---
runs: 3
max_turns: 120
allowed_tools: [Read, Grep, Glob, Write, Edit, Skill, Bash, Task]
---

/aantoniadis-skills:find-bugs thorough Review branch fix/force-retry-keeps-venv against main for defects. A Python environment with the project's runtime and test dependencies is at /tmp/real-pr-cache/pipx/venv/bin/python. The project itself is not installed there: set PYTHONPATH to the `src` folder of the checkout you test. `src/pipx/version.py` is generated at build time; copy it from this checkout into any other checkout you run. Tests that install packages from an index need the network; skip them. Install nothing and use no network.

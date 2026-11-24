---
type: llm
---

PASS if the message reports that a failed `install-all --force`, where the installed environment recorded a lock file and the spec entry has none, now leaves a half-built environment directory without `pipx_metadata.json`, because the failure handler changed to `if not exists` (install.py around line 304), where the base removed the half-built environment.
It counts in any section: a defect, a minor observation, an item outside the change, or a question.
FAIL if the message does not report it.

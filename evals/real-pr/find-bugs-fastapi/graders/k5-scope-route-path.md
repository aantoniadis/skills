---
type: llm
---

PASS if the final message reports that for a route reached through an included router, the route object in `request.scope["route"]` (its `.path` or `.path_format`) no longer carries the include prefixes, because the original route object is kept with its own local path, so code that reads `scope["route"].path`, such as metrics, tracing, or logging middleware, gets a path without the prefix where the base gave the full path. It counts as a defect, a minor observation, or a question.
FAIL if that is missing.

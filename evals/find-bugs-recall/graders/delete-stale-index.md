---
type: llm
---

PASS if the final message reports, as a defect of this change, that deleting a note leaves it in the search index: the new `store.delete` removes the file but nothing evicts its `index._cache` entry, so `index.search` and `batch.export_search` still return a deleted note. Either attribution (new, or made worse through the new delete path) counts.
FAIL if that defect is missing.

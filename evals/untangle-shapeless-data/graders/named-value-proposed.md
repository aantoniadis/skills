---
type: llm
---

Background: the pipeline passes one untyped hash through every step and each step writes into it.

PASS if the recommended rework in the final message gives the order a declared shape built once (for example a `Data.define`, a `Struct`, a value object, or a class with named fields) or has each step return its own result instead of writing into the shared hash.
FAIL if the recommendation keeps passing and changing the same hash, or if no rework is recommended and none of the alternatives above is mentioned.

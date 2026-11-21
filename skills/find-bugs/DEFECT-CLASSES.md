# Defect classes

Apply every class the unit lists. A source unit carries the eight classes
below; a prose, configuration, or fixture file carries **text** alone. A class
closes with the source fact that settles it: the guard that controls the value,
the consumer that handles the shape, the absence of the state it would corrupt.
**Not applicable** needs that fact and its line. A hunch closes nothing.

Record one short clause per class in the unit's sweep, and name the line you
read. When a class yields a defect, name the finding in the clause and keep it;
[step 4](SKILL.md#4-check-rank-and-deliver) decides whether the defect is
material. Keep observations, predictions, and intent distinct as
[EVIDENCE.md](../EVIDENCE.md) requires.

Read the sibling paths that produce the same effect: legacy, batch, retry,
cancellation, migration, and error paths beside the one that changed. Compare
what one component guarantees with what the next component assumes, and compare
sibling controls for equivalence rather than presence.

**boundary** — Under what accepted value does this line misbehave? Empty, zero,
one, negative, maximum, over-limit, missing, duplicate, malformed, and stale
values reach it through the callers you read. Ask what the first and last
iteration do, and what a division, index, or unpack does when the collection is
empty. Settled by a guard, a type, or a caller that cannot supply the value:
name it and its line.

**errors** — What state remains when this operation fails part-way? Read the
destructive steps and their order: delete, truncate, overwrite, move, publish.
Ask what a reader sees between the first write and the last, and what an
exception leaves behind: partial records, temporary files, held resources, a
cache that no longer matches the store. Settled by a rollback, an atomic
replace, a context manager, or a failure path that cannot be reached.

**state** — What shared or cached state does this change read, add to, or
invalidate? Module-level containers, caches, singletons, counters, and
registries survive between calls. Ask who else holds a copy, when it is
refreshed, and whether a removal evicts it. Settled by the invalidation call,
or by the fact that the state is per-call.

**consumers** — Who calls this symbol, and what does it newly call? Read the
consumers the ledger lists, including the ones the change does not touch, and
the existing functions the change newly calls or copies. Compare the signature,
return shape, ordering, units, exceptions, cleanup, and signals with what each
side assumes. A caller outside the diff breaks quietly; a producer used in a new
way may not offer what the new consumer needs. Settled by each listed consumer
and newly called producer read and matched, or named as unread with the reason.

**concurrency** — What happens when two of these run at once, or one is
cancelled? Shared temporary paths, shared containers, check-then-use sequences,
and asynchronous boundaries interleave. Ask what two workers with the same
input touch, and what a cancellation or timeout leaves running. Settled by a
lock, a path unique per call, an immutable value, or a single-threaded caller:
name it.

**normalization** — Does the value keep its identity through this change? Case,
encoding, whitespace, separators, slugs and ids, units, timezones, and
round-trips through a format. Ask what the rest of the system expects the
normalized form to be, and whether this path produces it. Settled by the shared
normalization function, or by a value that cannot vary.

**cost** — How does the work grow with the size of the input and the store? A
per-item scan of the whole collection, a refresh inside a loop, an unbounded
buffer, a retry without a limit. Ask what happens at a thousand times the tested
size, and count the work that grows — rescans, stats, reads, comparisons — at two
store sizes. A flat timing on one small case, or a read count that a cache keeps
flat while the rescan grows, settles nothing. Settled by a bound, or by a count
that stays flat per item as the store grows.

**compatibility** — What outside this change reads what it writes? Persisted
files, key and wire layouts, config defaults, public names, supported versions,
and consumers the project documents. Ask what an existing reader does with the
new form, and whether the old form still works. Settled by the project's own
convention, a migration, or a documented contract that the change keeps.

**text** — For prose, configuration, and fixtures: does the changed line
misstate a contract, weaken a check, or break a reader that relies on it? A
threshold, a dependency range, a CI step, a documented promise, and a fixture
that pins behavior all carry consequences. Settled by reading the line against
the code and the project's conventions that consume it.

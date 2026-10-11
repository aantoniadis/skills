# Dependency calls are cached per callable

**Bottom line:** the cache keeps overridden dependencies alive ([models.py:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140)); decide whether a weak-keyed cache is wanted.

**Reviewed:** head bbbbbbb against base aaaaaaa; merge base aaaaaaa. **Coverage:** `src/models.py` read at the line; one probe run.

## What the change does

Dependency flags are now computed once per callable and kept in a cache ([models.py:57-67](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L57-L67)).

## What to look at

1. **Overridden dependencies stay in memory** — *you decide* · *we ran it* · [details](#1-overridden-dependencies-stay-in-memory).
2. **Cache key ignores the callable's kind** — *check it* · *reasoned, not run* · [details](#2-an-override-with-another-kind-of-callable-may-be-misread).

## Possible bugs

### 1. Overridden dependencies stay in memory
*we ran it* · *new in this change*

**Where:** [models.py:57-67](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L57-L67), [:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140)
**Trigger:** a dependency override set per test, or an app built per tenant.

| | Base | Head |
| --- | --- | --- |
| Session captured by the override, after `overrides.clear()` | freed | still alive |

**Who / impact:** test suites that override a database dependency keep up to
1024 sessions reachable ([models.py:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140)); memory grows until eviction.
**Fix direction:** *Suggestion:* store the three flags on `Dependant` at construction.
**Reproduce:**
```sh
python runs/bugs/probe.py
```
Output: `head alive after overrides.clear(): True` · [script](runs/bugs/probe.py)

### 2. An override with another kind of callable may be misread
*suspected, not run* · *pre-existing, made worse*

**Where:** [models.py:170](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L170)
**Trigger:** an async dependency overridden by a sync one.

| | Base | Head |
| --- | --- | --- |
| Flags for the override | predicted: computed for the override | predicted: read from the original's cache entry |

**Who / impact:** apps that override async dependencies with sync stubs; predicted: the stub is awaited.
**Fix direction:** *Suggestion:* key the cache on the override, not the original.
**Probe that would settle it:** override an async dependency with a sync function and call the endpoint at base and head.

## Requirements

| Requirement and intent | Status | Behavior and evidence | Next action |
| --- | --- | --- | --- |
| "Cache dependency flags" ([PR.md:1](https://github.com/acme/widgets/blob/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/PR.md#L1)) | Partial | [Cached flags](#cached-flags): the cache works but holds callables | Decide on a weak-keyed cache |

## Questions for the author

Should the cache hold callables weakly? See [Cached flags](#cached-flags).

## Behavior changes

### Cached flags

**Purpose and tradeoff:** computing flags once trades memory for speed ([models.py:57-67](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L57-L67)).

**Conditions:** a dependency is resolved more than once ([models.py:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140)).

| Scenario | Before | After | Consumer consequence | Evidence |
| --- | --- | --- | --- | --- |
| Repeated request | Flags computed per request | Flags read from the cache | Faster requests | [models.py:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140) |

**Consumers:** request handlers; other callers not inspected.

**Preserved:** the dependency signature is unchanged ([models.py:57](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L57)).

**Open question:** should the cache hold callables weakly?

## Verification

Tests inspected: none. Recorded runs: none. Executed: one probe.

| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |
| --- | --- | --- | --- | --- |
| [Cached flags](#cached-flags) | Not run | Source inspected | bbbbbbb; source only | Prediction only |
| [Bug probes](#possible-bugs) | Failed | Executed here | bbbbbbb against aaaaaaa; one probe | An override with another kind of callable stays suspected |

## Evidence and record

### Gaps

This synthetic fixture establishes report shape only.

### Changed files

[models.py](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py): cached flags; synthetic source inspection.

### Provenance

Synthetic test fixture, not an actual review or execution result.

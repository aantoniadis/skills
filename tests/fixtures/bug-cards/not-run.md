# Dependency calls are cached per callable

**Bottom line:** the cache keeps overridden dependencies alive ([models.py:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140)); decide whether a weak-keyed cache is wanted.

**Reviewed:** head bbbbbbb against base aaaaaaa; merge base aaaaaaa. **Coverage:** `src/models.py` read at the line; one probe run.

## What the change does

Dependency flags are now computed once per callable and kept in a cache ([models.py:57-67](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L57-L67)).

## What to look at

1. **The cache holds callables** — *you decide* · *read at the line*
   The cache keeps every callable ([models.py:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140)).
   Look at: [models.py:140](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L140).
   Settle: should the cache hold callables weakly?

## Possible bugs

The search for bugs has not run: the review stopped after the overview.

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
| [Bug probes](#possible-bugs) | Not run | Proposed | bbbbbbb; no probe ran | No path was probed |

## Evidence and record

### Gaps

This synthetic fixture establishes report shape only.

### Changed files

[models.py](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py): cached flags; synthetic source inspection.

### Provenance

Synthetic test fixture, not an actual review or execution result.

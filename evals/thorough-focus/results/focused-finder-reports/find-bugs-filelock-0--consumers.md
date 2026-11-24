Six candidates hold up against base and head. Four come from executed probes run at both base and head (a fifth result in the same probes is head-only). One is inferred from the docs and checked against probe 2. This was one read, limited to what code outside the change sees.

All paths below are relative to `<scratch>/out-arm/find-bugs-filelock-0/.scratch/strict-owner-claims/search-1/finder-consumers/`. That folder holds base worktree `base/` (126cab7) and head worktree `head/` (e6538e1), with `version.py` copied into both. Probe scripts, outputs and exact commands are in `probes/`, with the commands in `probes/COMMANDS.txt`. Every probe prints `filelock.__file__`, which confirmed the worktree's `src/` was loaded each time. The checkout itself is unchanged.

## Candidates

**1. A `release()` from another thread blocks, then releases a lock the waiting thread has just acquired (executed)**
- **Location:** `src/filelock/_api.py`, `BaseFileLock.release`. The gate `with self._transition_lock if serialize ...` is taken before the `not self.is_locked` check. `_transition_admission` holds that same RLock through the whole `_poll_until_acquired` wait.
- **Trigger:** a shared `StrictSoftFileLock(path, thread_local=False)`.
  - Thread A calls `acquire(timeout=5)` while a different instance holds the path.
  - Thread C calls `shared.release()` while A is still waiting.
- **Base:** C's release is a no-op and returns in 0.0 s. A acquires and stays holding (`is_locked True`, counter 1).
- **Head:** C blocks for 1.04 s, until A acquires. C then fully releases A's new hold, so A's protected body runs with `is_locked False`, counter 0.
- **Contract broken:** `release()` on an instance that is not held must be a no-op. Mutual exclusion for thread A is lost silently.
- The async path (`asyncio.py`, `release`) checks `is_locked` before its gate, so only the sync path has this.
- **Probe:** `probes/p1_release_while_waiting.py`, output in `probes/p1.out`.

**2. A non-blocking re-entry into an already-held shared instance raises `Timeout` (executed)**
- **Location:** `src/filelock/_api.py`, `_transition_admission`. With `blocking=False`, a busy gate raises `Timeout` before the code reaches the `is_locked` check that would simply bump the counter.
- **Trigger:** the main thread holds `StrictSoftFileLock(path, thread_local=False)`. Two threads loop on `acquire(blocking=False)` / `release()`.
- **Base:** 0 timeouts in 40,000 attempts.
- **Head:** 20,000 spurious `Timeout`s, even though the instance holds the lock the whole time.
- The same applies to a `timeout=` wait that runs out while another thread is only briefly inside acquire or release.
- **Contract broken:** re-entering a lock the instance already holds must not fail.
- **Probe:** `probes/p3_nonblocking_reentrant.py`, output in `probes/p3.out`.

**3. After any strict use, `SoftFileLease` is locked out of the path for good, which contradicts the docs (executed)**
- **Location:** the permanent sentinel written by `_open_or_create_sentinel` in `src/filelock/_strict.py`. `SoftFileLease._try_break_stale_lock` in `src/filelock/_lease.py` never breaks a record it cannot parse, and the sentinel is one of those.
- **Trigger:** `with StrictSoftFileLock(p): pass`, then `SoftFileLease(p, lease_duration=60, timeout=1)`.
- **Base:** the lease enters.
- **Head:** `Timeout`, with no strict holder present.
- **Contract broken:** the table in `docs/how-to.rst` (around line 674) says "The lease waits out a strict holder". The new concepts text mentions the lockout only for legacy `SoftFileLock` clients, not for leases.
- **Probe:** `probes/p2_mixed_contracts_and_lifetime.py`, case 2, output in `probes/p2.out`.

**4. The "Choose a soft-lock contract" section of `docs/how-to.rst` (about lines 625–675) still describes the old design (inferred; checked against probe 2)**
The section still describes the marker-based strict lock that the change removed:
- "StrictSoftFileLock never reclaims a marker"
- force_break linked as `filelock.MarkerSoftFileLock.force_break`. At head the class derives from `BaseFileLock` and its `force_break(claim_name)` requires an argument.
- "Both classes publish a protocol 2 record"
- The table row "SoftFileLock with StrictSoftFileLock — No. The legacy contender evicts the protocol 2 marker."

Probe 2 case 4:
- **Base:** `SoftFileLock entered while strict holds`.
- **Head:** `SoftFileLock Timeout while strict holds`, because the new check in `_soft.py` skips the sentinel. The lease row is wrong as described in candidate 3.

Probe that would show it: build the docs, or compare the table with probe 2's output, as above.

**5. The `lifetime` warning for `StrictSoftFileLock` gives the native-lock reason (executed, minor)**
- **Location:** `src/filelock/_strict.py`, class attributes. The `_lifetime_unsupported_reason` override was dropped when the base class changed from `MarkerSoftFileLock` to `BaseFileLock`, so it falls back to `BaseFileLock`'s text.
- **Trigger:** `StrictSoftFileLock(p, lifetime=5)`.
- **Base:** "...a strict lock never reclaims a marker by age...".
- **Head:** "...a native OS lock cannot be broken safely by file age...".
- **Contract broken:** the warning text in the `_api.py` metaclass call states the backend's own reason.
- **Probe:** `probes/p2_mixed_contracts_and_lifetime.py`, case 1.

**6. `SoftFileLock(path).pid` reports PID 1 forever on a path that strict mode has used (executed, minor)**
- **Location:** `STRICT_SOFT_SENTINEL_RECORD` in `src/filelock/_soft_protocol.py`. `"1\nfilelock-strict-v1\x00\n0\n"` parses as pid 1 in `_parse_lock_holder`.
- **Base:** `None` during and after a strict hold.
- **Head:** `1` during the hold and after release.
- **Contract broken:** the `SoftFileLock.pid` docstring says it returns "the PID of the process holding this lock", or `None` when none can be parsed. Blocking legacy clients this way looks deliberate; only the inspection result is misleading.
- **Probe:** `probes/p4_generic_protocols.py`, output in `probes/p4.out`.

## Dropped leads
- **`SoftFileLockProtocolError` with pickle, copy, deepcopy and `str`:** all round-trip with the same message, `claim_name` and `reason` (p4). `errno` is `None`, which is normal for an `OSError` built from one argument.
- **`StrictSoftFileClaim` equality, hash and pickle:** all work (p4).
- **Removed `owner`, `pid`, `is_lock_held_by_us` and no-argument `force_break()` on `StrictSoftFileLock`:** the base strict class exists only in the unreleased fragment `docs/changelog/636`, so there is no released API to break.
- **`_poll_delay` for other backends:** `_poll_backoff_cap=0` returns `poll_interval` unchanged. With `poll_interval=0` the strict case gives 0, the same as base.
- **Async `AsyncStrictSoftFileLock` gate and `claim_root`:** release checks `is_locked` before the gate, and `claim_root` is cleared in `finally`. The only difference is that async polling has no jittered backoff, which is a design gap, not a defect.
- **Fork child deadlocking on a `_transition_lock` held at fork:** every registered instance gets `_reset_after_fork_in_child`, which replaces the RLock and clears the claim state (`_api.py`, `_detach_child_state`).
- **Overrides of `acquire`, `_poll_until_acquired` or `release` in other `BaseFileLock` subclasses:** none outside `asyncio.py`. The read-write classes override `_reset_after_fork_in_child` but are not `BaseFileLock` subclasses.
- **`cancel_check` callback during the admission wait:** it is now also called while waiting for the gate, and raises `Timeout` as documented. A `release()` from inside the callback is reentrant on the RLock and a no-op.
- **`SoftFileLock` sentinel early return in `_try_break_stale_lock`:** this is the intended lockout of legacy clients, documented in `docs/concepts.rst`. It is covered only for the doc staleness in candidate 4.
I did one read of the shared state this change adds: the per-instance gate `_transition_lock`, which lazily creates `_context.claim_root`, plus `_context.owner_claim_paths`, the import-time capability flags and the fork reset. Two candidates held up, and both ran at base and head. The checkout is unchanged. Probes, commands and output are in `<scratch>/out-arm/find-bugs-filelock-2/.scratch/strict-owner-claims/search-1/finder-state/`: the scripts are `p1_nonblocking_reentrant.py` and `p2_release_blocks.py`, the exact command is in `COMMANDS.txt`, and the output is in `probes_p1_p2.log`.

## Candidates

**1. A shared lock this process already holds now refuses non-blocking re-entry with spurious `Timeout`s (executed)**
- **Location:** `src/filelock/_api.py:1100-1104` (`_transition_admission`), together with `_serialize_transitions = True` at `src/filelock/_strict.py:80`.
- **Trigger:** `StrictSoftFileLock(path, thread_local=False)` is already held by this process. Other threads call `acquire(blocking=False)` (or use a short timeout) while any thread is inside the gate. Even a re-entry that only bumps the counter holds the gate.
- **Base result:** `ok=32000 timeouts=0`.
- **Head result:** `ok=2000 timeouts=30000`, with 16 threads × 2000 non-blocking re-entries each.
- **Contract broken:** a shared, held instance is reentrant across threads. `blocking=False` should fail only when the lock "cannot be obtained", but here the lock is already held by this same instance. With `blocking=True`, every re-entry that meets the gate also sleeps a full `poll_interval` (default 0.05 s).
- **Probe:** `p1_nonblocking_reentrant.py`.

**2. `release()` on an unheld shared instance blocks until another thread's acquire finishes (executed)**
- **Location:** `src/filelock/_api.py:1121-1124`. `release()` takes `_transition_lock` with a blocking `with` before it checks `_creator_pid` or `is_locked`. In base those checks returned at once.
- **Trigger:** a shared strict instance (`thread_local=False`) is not held. Thread W is in `acquire(timeout=5)` waiting on an outside holder, so W holds the gate for its whole wait. Another thread calls `shared.release()` or `release(force=True)`.
- **Base result:** returns immediately (elapsed 0.00).
- **Head result:** still blocked after 1.5 s. It returned only after W's acquire finished (1.52 s). With `timeout=-1` it would block for as long as the outside holder keeps the lock.
- **Contract broken:** releasing an unheld lock is a no-op. A release call such as cleanup or `finally: release()` must not wait on another thread's acquisition.
- **Probe:** `p2_release_blocks.py`.

## Dropped leads
- **Bypassing the deadlock check by waiting at the gate (hang instead of `RuntimeError`):** base hangs too. Because the counter is shared, the second thread sees `lock_counter == 2`, so `_raise_if_would_deadlock` (`_api.py:1192`) is skipped in base as well.
- **Async strict instances missing `_transition_lock`, since `BaseAsyncFileLock.__init__` does not call super:** async overrides `acquire` and `release` and never reads it. `serialize` evaluates the lock only when true, and `_reset_after_fork_in_child` assigns it.
- **Async race on `claim_root` or `owner_claim_paths`:** async acquire and release are already serialized by the existing `_transition_gate`. A thread-local context with an executor is rejected (`asyncio.py:93`).
- **Stale `claim_root` across acquisitions or `chdir`:** `_release` clears it at `_strict.py:198`, and `_reconcile_failed_acquire` clears it when the lock is not held (`_strict.py:192`). Admission refusal now happens before any state is touched.
- **`claims` or `force_break` reading `owner_claim_paths` mid-doorway from another thread:** every value points at the same claim directory, and the path is absolute once the lock is held.
- **Fork child inheriting a held gate:** `_detach_child_state` calls `_reset_after_fork_in_child` on every registered instance (`_api.py:1760`), and that resets the RLock and the claim fields. `__del__` checks the pid before calling `release`.
- **Singleton re-init replacing `_transition_lock` while it is held:** the metaclass returns the cached instance without calling `__init__` again (`_api.py:401-410`).
- **Gate-wait overshooting the timeout when `poll_interval` > `timeout`:** base `_poll_until_acquired` overshoots the same way.
- **`_poll_delay` with a zero or negative `poll_interval`:** same busy-loop or `ValueError` as base.
- **Import-time `_LINK_HONORS_FOLLOW_SYMLINKS` probe failing, for example when TMPDIR is unwritable:** it falls back to False, which is safe because the link source is an O_EXCL file this process created.
- **`SoftFileLock` never breaking a file holding the strict sentinel:** this is persistent file state rather than in-process shared state, it is outside this search's focus, and the project documents that the two classes do not interoperate.
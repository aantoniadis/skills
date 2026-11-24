I found three candidates that I could not contradict. All are about state that outlives one call. Each one has a probe I ran at base and at head. Files are under `<scratch>/out-arm/find-bugs-filelock-1/.scratch/strict-owner-claims/search-1/finder-state/`. That folder holds base and head copies of `src` (made with `git archive`, plus `version.py`), the probes, their outputs, and `probes/COMMANDS.txt`. The reviewed checkout is unchanged.

Every probe ran as:
`for v in base head; do PYTHONPATH=$PWD/$v/src timeout 20 /tmp/real-pr-cache/filelock/venv/bin/python probes/<probe>.py; done`, run from `finder-state/`.

## Candidates

**C1. A held lock shared across threads refuses re-entry when the caller does not wait**
- **Location:** `src/filelock/_api.py`, `_transition_admission`, the loop `while not self._transition_lock.acquire(blocking=False): if not blocking ...: raise Timeout`. The gate is also taken in `release()`.
- **Trigger:** a `StrictSoftFileLock(thread_local=False)` that is already held. One thread calls `acquire(blocking=False)` (or `timeout=0`) while another thread is briefly inside the gate, either re-entering or releasing with a counter above 1. It also applies to `timeout=T` if the gate is held longer than T.
- **Base:** re-entry always succeeds and only bumps the counter.
- **Head:** raises `Timeout` even though this instance already holds the lock.
- **Contract broken:** `thread_local=False` makes the lock re-entrant across threads, so acquiring an instance that already holds the lock should never fail.
- **Probes:**
  - `p1_reentrant_nonblocking.py` widens the window with a 0.4 s sleep in thread C. Output in `p1.out`: base `B: acquired (reentrant)`, head `B: Timeout`.
  - `p1b_reentrant_nonblocking_stress.py` has no instrumentation: 4 threads loop `acquire(blocking=False)`/`release` for 2 s. Output in `p1b.out`: base `{'ok': 36184, 'timeout': 0}`, head `{'ok': 567, 'timeout': 693264}`.

**C2. `release()` on an unheld shared lock blocks until another thread's `acquire()` finishes**
- **Location:** `src/filelock/_api.py`, `release()`, the line `with self._transition_lock if serialize else contextlib.nullcontext():`. It takes the gate with a blocking wait and no timeout, before the `not self.is_locked` early return. The gate is held for the whole wait inside `_poll_until_acquired`.
- **Trigger:** thread A is in `shared.acquire(timeout=-1)`, waiting on another holder. Thread B calls `shared.release()`.
- **Base:** returns immediately (0.00 s) as a no-op.
- **Head:** blocks until A's acquire ends: 1.54 s in the probe. It blocks forever if the holder's release depends on B, for example if B releases `shared` and then the holder.
- **Contract broken:** releasing a lock that is not held is an immediate no-op.
- **Probe:** `p2_release_blocks.py`, output in `p2.out`. The first version hung at head until the 20 s timeout. That was because its holder was thread-local, so the Timer thread could not release it. I fixed it to `thread_local=False`, and that version is the one recorded.

**C3. `AsyncStrictSoftFileLock` does not use the jittered contention backoff**
- **Location:** the backoff lives in `src/filelock/_api.py` (`_poll_delay`, used only by the sync `_poll_until_acquired`) and is configured by `_strict.py` (`_poll_backoff_cap = 0.05`). `src/filelock/asyncio.py` `_async_poll_until_acquired` still calls `await asyncio.sleep(poll_interval)`. The async class inherits the cap but never reads it.
- **Trigger:** any async strict waiter under contention.
- **Base:** neither variant backs off.
- **Head:** the sync waiter's sleeps are jittered (13 distinct values: 0.005, 0.0172, 0.0233, ...), while the async waiter keeps a fixed cadence (1 distinct value, 0.005).
- **Contract broken:** the change's own comment says the multi-file backend sets the cap "so contending processes desynchronize instead of livelocking". Async contenders get no such protection.
- **Probe:** `p3_async_backoff.py`, output in `p3.out`. It shows only the sleep cadence. It does not demonstrate an actual livelock.

## Dropped leads
- **The singleton could re-run `__init__` and replace `_transition_lock` while it is held:** the singleton path in `FileLockMeta` returns the cached instance and does not call `__init__` again.
- **Async strict instances lack `_transition_lock`, since `BaseAsyncFileLock.__init__` does not set it:** async overrides `acquire` and `release` and uses its own `_transition_gate`. Nothing calls the sync `release` on an async instance.
- **`__del__` → `release(force=True)` could block on the gate from a GC thread:** `__del__` only runs when nothing references the instance, so no other thread can be in `acquire`. The `RLock` is re-entrant on the same thread.
- **`owner_claim_paths` or `claim_root` overwritten by concurrent acquirers on one instance:** sync shared contexts are serialized by the new gate, async ones by `_transition_gate`, and thread-local contexts are separate per thread.
- **Async clears `claim_root` in `finally`, even on a re-entrant acquire:** `_acquire` only reads `claim_root` while acquiring, and `_release` clears it too, so there is no observable effect.
- **Stale `claim_root` after a failed sync acquire:** `_reconcile_failed_acquire` clears it when the lock is not held. When `_discard_doorway` commits a held claim, it stays until `_release` clears it, which is intended.
- **Fork reset of `_transition_lock`, `owner_claim_paths` and `claim_root`:** the child gets an unheld gate and owns no claims, which is correct.
- **Import-time `_LINK_HONORS_FOLLOW_SYMLINKS` probe failing without a temp directory:** `FileNotFoundError` is an `OSError` and is caught, so the probe returns False and the plain `os.link` is safe for a private O_EXCL source.
- **`_poll_delay` overflow or poll_interval edge cases:** the exponent is capped at 20, and `max(poll_interval, …)` keeps the floor. `poll_interval=0` busy-polls exactly as base does.
- **`_claim_directory` / `force_break` after a working-directory change:** a holder uses the absolute `owner_claim_paths[0]`. A non-holder resolves against the current directory, which is the same as how `lock_file` itself is resolved.
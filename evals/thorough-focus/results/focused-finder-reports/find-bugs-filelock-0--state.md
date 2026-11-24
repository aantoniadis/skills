I found two candidates in the new shared state that I could not contradict. Both were run at base and at head. The checkout at e6538e1 is unchanged, and I started no workers.

Probes, outputs and the exact commands are saved in `<scratch>/out-arm/find-bugs-filelock-0/.scratch/strict-owner-claims/search-1/finder-state/` (commands in `COMMANDS.txt`). The base run uses a disposable worktree at `.../finder-state/base` (126cab7, with `version.py` copied in). Each run printed `filelock.__file__` to confirm it loaded the intended `src`.

## Candidate 1 (executed): `release()` on a lock nobody holds now waits for another thread's acquire, and can deadlock

- **Location:** `src/filelock/_api.py:1121-1124`. `release()` takes `self._transition_lock` with a blocking `with` *before* it checks `if self._creator_pid != os.getpid() or not self.is_locked: return`. Meanwhile `_transition_admission` (`_api.py:1100-1109`) holds that same lock for the whole `_poll_until_acquired` wait.
- **Trigger:** a `StrictSoftFileLock` shared between threads (`thread_local=False`):
  - Thread A is waiting in `acquire()` because someone else holds the path.
  - Thread B calls `shared.release()` on that instance while it is not held. A common case is `try: lock.acquire(timeout=...) except Timeout: ... finally: lock.release()`.
- **Base result:** `release()` returns in 0.0 s, so it does nothing, as before.
- **Head result:**
  - `release()` blocks until A's acquire ends: 2.73 s against A's 3 s timeout. With `timeout=-1` it would block forever.
  - Deadlock variant: thread B holds the path through a second instance and its cleanup calls `shared.release()` and then `holder.release()`. B never reaches `holder.release()`, so A never acquires. After 5 s, base prints `A acquired: True`, `B finished: True`; head prints `False`, `False`.
- **Contract broken:** calling `release()` on a lock you do not hold should do nothing and return at once. The async counterpart (`asyncio.py:462`) checks `is_locked` *before* taking its gate, so only the sync path behaves this way.
- **Probes:** `probe_release_blocks.py` / `.out` and `probe_release_deadlock.py` / `.out`.

## Candidate 2 (executed / inferred): the jittered backoff does nothing at the default poll interval, and the async lock has none

- **Location:** `src/filelock/_api.py:1238-1247` (`_poll_delay`), `src/filelock/_strict.py:83` (`_poll_backoff_cap = 0.05`), and `src/filelock/asyncio.py:373`.
- **Trigger:**
  - Sync `StrictSoftFileLock` with the default `poll_interval=0.05`, or any value at or above 0.05: the window is `min(0.05, ...) = 0.05`, and `max(poll_interval, U[0, 0.05])` always equals `poll_interval`.
  - `AsyncStrictSoftFileLock` at any setting: `_async_poll_until_acquired` still calls `asyncio.sleep(poll_interval)` and never uses `_poll_delay`.
- **Base result:** fixed retry cadence (the feature did not exist).
- **Head result:**
  - At `poll_interval=0.05`, 1960 samples gave exactly one distinct delay (0.05). At 0.1, one distinct delay (0.1).
  - Only below the cap does it jitter: at 0.01 there were 1516 distinct delays.
  - Async: fixed cadence at every setting (inferred from source; the grep is saved).
- **Contract broken:** commit b072b3b says contending processes should "desynchronize" through a "jittered, exponentially widening window" so a contended strict lock does not livelock. At default settings, and for every async strict lock, contending processes still retry on the same schedule. This is weaker than Candidate 1: the commit's own trigger was a 0.5 ms poll, which does get jitter.
- **Probe:** `probe_backoff_default.py` / `.out`. To fully confirm the async half, run a multi-process async contention stress test.

## Dropped leads
- **Async locks never set `_transition_lock`** (their `__init__` skips the base one): the only users are the base sync `acquire`/`release`, which the async class overrides. The fork reset assigns it anyway.
- **Sync acquire leaves `claim_root` set after success, while async clears it:** `_acquire` reads it only while the lock is not held, and `_release` and the strict `_reconcile_failed_acquire` clear it. Nothing reads it stale.
- **Two threads or tasks writing `claim_root` / `owner_claim_paths` at once:** a shared sync instance is serialized by the gate, a thread-local context is per thread, and async is serialized by `_transition_gate`. Thread-local with `run_in_executor` is outside this search.
- **A non-blocking acquire on a shared instance gets `Timeout` while another thread is releasing it:** that reports contention, which non-blocking callers must already handle.
- **The gate spins when `poll_interval=0`:** base's poll loop spins the same way.
- **`_claim_directory` uses the current working directory when nothing is held:** that is how `claims`/`force_break` already worked, and when the lock is held it uses `owner_claim_paths`.
- **Fork while a parent thread holds the gate or is mid-doorway:** `_reset_after_fork_in_child` (`_api.py:1166-1168`) replaces the RLock and clears `owner_claim_paths` and `claim_root`.
- **Import-time capability probes** (`_strict.py:49-71`): read-only constants, and the link probe returns False on any error, including an unusable TMPDIR.
- **Backoff exponent overflow:** capped at 2**20.
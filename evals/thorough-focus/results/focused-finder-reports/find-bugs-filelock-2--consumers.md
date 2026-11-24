I searched the consumer-facing surface of the change in one read and started no workers. I have six candidates I could not contradict, five of them with saved probes run at base and head. Everything is saved in `<scratch>/out-arm/find-bugs-filelock-2/.scratch/strict-owner-claims/search-1/finder-consumers/`. Each probe is a `.py` file with its output in a matching `.out` file.

Every probe was run as `PYTHONPATH=<wt-base|wt-head>/src /tmp/real-pr-cache/filelock/venv/bin/python <probe>.py`.

## Candidates

**1. Every lock class can no longer be pickled or deep-copied.**
- **Location:** `src/filelock/_api.py` `BaseFileLock.__init__`, the line `self._transition_lock = RLock()`. It runs for every class, not only the strict lock.
- **Trigger:** `pickle.dumps(...)` or `copy.deepcopy(...)` on any lock built with `thread_local=False`, such as `FileLock`, `SoftFileLock` or `StrictSoftFileLock`. Passing such a lock to a worker started with multiprocessing spawn does the same.
- **Base:** pickle and deepcopy both succeed.
- **Head:** `TypeError: cannot pickle '_thread.RLock' object`.
- **Contract broken:** an existing generic protocol on public classes, broken for classes that do not use the new gate. No `__getstate__` drops the RLock.
- **Probe:** `probe_protocols.py` / `probe_protocols.out`.

**2. Calling `release()` on an instance shared between threads can block for the other thread's whole acquire timeout.**
- **Location:** `src/filelock/_api.py` `BaseFileLock.release`. It takes `_transition_lock` before the `not self.is_locked` early return. `acquire` holds that same lock for the entire poll.
- **Trigger:** a `StrictSoftFileLock(thread_local=False)` is shared between threads. Thread A waits in `acquire(timeout=T)` while another owner holds the path. Thread B then calls `release()` or `release(force=True)`, for example in a shutdown or cleanup path.
- **Base:** the release returns in 0.00s.
- **Head:** the release blocks 1.82s, until A's 2s acquire timed out. With `timeout=-1` it would block indefinitely.
- **Contract broken:** a release of an unheld lock is a no-op that returns at once.
- **Probe:** `probe_release_gate.py` / `probe_release_gate.out`.

**3. On a filesystem whose `link()` fails with EPERM, acquire raises a plain `PermissionError`, not the documented `SoftFileLockProtocolError`.**
- **Location:** `src/filelock/_strict.py` `_raise_if_hard_links_unsupported`. It only recognises the error codes ENOSYS, ENOTSUP and EXDEV.
- **Trigger:** the Linux `link(2)` man page says EPERM means "the filesystem ... does not support the creation of hard links", as on vfat or exFAT. The probe injects that error by replacing `os.link`; no real vfat mount was tested.
- **Base:** the old marker-based strict lock acquires normally.
- **Head:** `PermissionError [Errno 1]`, not a `SoftFileLockProtocolError`.
- **Contract broken:** `docs/how-to.rst` says "If hard-link publication is unavailable, acquisition raises SoftFileLockProtocolError", and `docs/concepts.rst` makes the same promise.
- **Probe:** `probe_eperm_link.py` / `probe_eperm_private.out`.

**4. The how-to page and the 636 changelog fragment still describe the old strict lock.** (Stale documentation.)
- **Location:**
  - `docs/how-to.rst`, the section "Choose a soft-lock contract" (around lines 621–675).
  - `docs/changelog/636.feature.rst`.
- **What they say:**
  - `StrictSoftFileLock` "never reclaims a marker".
  - Clear a stale lock with `MarkerSoftFileLock.force_break`, taking no argument.
  - "Both classes publish a protocol 2 record".
  - The compatibility table says `SoftFileLock` with `StrictSoftFileLock` gives "No. The legacy contender evicts the protocol 2 marker".
  - The table says a lease "waits out a strict holder".
- **Head behaviour, from the probe:**
  - The path survives the strict release as a permanent sentinel file.
  - `SoftFileLock` and `SoftFileLease` time out even after the strict holder has released.
  - `force_break()` with no argument raises `TypeError` because `claim_name` is now required.
  - `StrictSoftFileLock` is no longer a subclass of `MarkerSoftFileLock` or `SoftFileLock`.
  - `owner`, `pid`, `is_lock_held_by_us` and `break_lock` are gone.
- **Base:** the documentation matched the code.
- **Contract broken:** the new section in the same file and `concepts.rst` contradict it, and both changelog fragments would ship together.
- **Probes:** `probe_doc_matrix.py` / `.out` and `probe_protocols.out`.

**5. The jittered retry backoff does nothing at the default `poll_interval`.**
- **Location:** `src/filelock/_api.py` `_poll_delay`, together with `_poll_backoff_cap = 0.05` in `_strict.py`.
- **Trigger:** the default `poll_interval` is 0.05. The window is capped at 0.05 and the result is then raised back to at least `poll_interval`, so it is always exactly 0.05.
- **Base:** no backoff existed.
- **Head:** 980 samples at the default interval gave one distinct delay, 0.05. At `poll_interval=0.01` they spread from 0.01 to 0.05.
- **Contract broken:** the code comment says contending processes "desynchronize instead of livelocking". The effect on actual livelock is not measured.
- **Probe:** `probe_poll_delay.py` / `probe_poll_delay.out`.
- **Related (inferred):** `AsyncStrictSoftFileLock`'s poll loop in `src/filelock/asyncio.py` (around line 372) sleeps a fixed `poll_interval` and never calls `_poll_delay`, so the async lock gets no backoff at any interval. Probe to run: `inspect.getsource(BaseAsyncFileLock._async_poll_until_acquired)`, or a patched `asyncio.sleep` that records its delays while contended.

**6. A damaged private record in the claims folder produces an error with no useful detail.**
- **Location:** `src/filelock/_strict.py`. `_reclaim_private_record` raises `OSError(msg)`, which has no errno. `_read_claims` wraps it as "cannot list claim directory: {strerror or type name}".
- **Trigger:** a directory (or other non-file entry) at a `.…private-v1-….tmp` name in `claims/`.
- **Base:** no such class existed.
- **Head:** `lock.claims` and `acquire` raise `SoftFileLockProtocolError` with `claim_name=None` and `reason='cannot list claim directory: OSError'`. The offending entry name is lost.
- **Contract broken:** the how-to says the exception's `claim_name` "identifies the entry that needs inspection". That sentence is written for claims, but an operator recovering from this damage gets no pointer to the entry.
- **Probe:** `probe_private_nonregular.py` / `probe_eperm_private.out`. The base run fails on an import error because the class is new.

**Minor:** `StrictSoftFileLock(lifetime=...)` now warns "a native OS lock cannot be broken safely by file age", which is wrong for this class; base said "a strict lock never reclaims a marker by age". The class sets no `_lifetime_unsupported_reason`, so it inherits the native-lock text. Seen in `probe_protocols.out`.

## Dropped leads
- **Async shared instance missing the new sync gate:** `BaseAsyncFileLock` already serialises acquire and release through `_transition_gate`, so it needs no gate of its own.
- **Async `claim_root` reset in `finally` after a successful acquire:** the held lock's `_claim_directory` uses `owner_claim_paths`, and `_release` doesn't read `claim_root`.
- **`SoftFileLock` sentinel check hiding `lifetime` expiry:** expiry runs separately in `_try_break_expired_lock`, as the docs say.
- **`SoftFileLease` evicting the sentinel:** `parse_marker` returns None for the protocol-1 sentinel and `_try_break_stale_lock` returns, so the lease waits.
- **`on_acquired` rejection as a regression:** the base strict class already had `_on_acquired_supported=False` through `SoftFileLock`.
- **Removed base API (`owner`, `pid`, `is_lock_held_by_us`, no-argument `force_break`) as a compatibility break:** the base class carries `versionadded 3.30.0` and the repository has no release tags, so it looks unreleased. It is kept only as stale documentation in item 4.
- **The `_reset_after_fork_in_child` additions:** they only reset per-instance state and touch no shared object.
- **Pickling `SoftFileLockProtocolError` and `StrictSoftFileClaim`:** the error defines `__reduce__`, and the claim is a frozen dataclass of plain values.
- **Deadlock through the RLock on reentrant acquire in the same thread:** an RLock lets the same thread take it again.
- **Non-blocking acquire against a busy gate:** it raises `Timeout` at once, like base.
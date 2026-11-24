I did one read of the change (base 126cab74, head e6538e1d) and found five candidates I could not contradict. Four were run on both base and head; C3 was run on head only, with the base result inferred from the source. The probes, their outputs and a command index are in `<scratch>/out-arm/find-bugs-filelock-2/.scratch/strict-owner-claims/search-1/finder-general/` (`probes/*.py`, `probes/*.out`, `notes.md`). Each probe runs as `PYTHONPATH=../../wt-{base,head}/src /tmp/real-pr-cache/filelock/venv/bin/python probes/<probe>`, with the same Python as root on Linux. The checkout and worktrees are unchanged.

One environment note: the head test `test_strict_soft_unreadable_claim_fails_closed` fails here only because the tests run as root, which can read files whatever their permissions. It is not a finding.

## Candidates

**C1. A retry `acquire()` returns success while another instance holds the lock (executed, fault injected).**
- **Location:** `src/filelock/_strict.py:211-216` (`_discard_doorway` marks the sentinel descriptor as owned when its own claim cannot be removed), together with `_rollback_failed_acquire` at 181-188 and `_api._reconcile_failed_acquire`, which commits that state.
- **Trigger:**
  1. L enters the doorway, and H acquires between L's first scan and L's intent publication. This interleaving is forced in the probe.
  2. L's rescan sees H's held claim, so L backs off.
  3. Unlinking L's own intent fails once (EACCES injected; EIO or a filesystem remounted read-only would do the same).
  4. `acquire()` raises, but `L.is_locked` stays True with only an intent claim on disk.
  5. Any retry, such as `L.acquire()` or another `with L:`, takes the reentrant path, raises the counter to 2 and returns success.
- **Head:** `L retry acquire: SUCCESS ... H.is_locked = True ... OVERLAP`
- **Base:** in the same contention, L times out on both attempts and `is_locked` is False. Base has no doorway, so `p2_base_equivalent.py` is the closest equivalent scenario.
- **Contract broken:** mutual exclusion, and `is_locked` meaning that this instance holds the lock. The head test `test_strict_soft_doorway_preserves_every_claim_cleanup_error` asserts `is_locked == True` in this state, but it never retries the acquire.
- **Probe:** `p2_stuck_intent_reentrant.py`, outputs `p2.out` and `p2_base.out`.

**C2. A second OS user cannot acquire a shared strict lock (executed).**
- **Location:** `_strict.py:773-783`. `_ensure_protocol_directory` uses a plain `mkdir()`, so `<path>.filelock` and `claims` get the umask permissions (0755) and ignore the `mode` argument.
- **Trigger:**
  1. User A (umask 022, `mode=0o666`) acquires and releases a lock in a sticky world-writable directory.
  2. User B (uid 65534) tries to acquire the same lock.
- **Head:** `user B raised PermissionError [Errno 13] ... .intent-v1-....tmp`. This is an error, not a Timeout, and it happens every time from then on.
- **Base:** `user B acquired`.
- **Contract broken:** the `mode` parameter, which exists for lock files shared between users, no longer makes the lock usable by other users.
- **Probe:** `p5_multiuser.py`, output `p5.out`.

**C3. After any strict use, `SoftFileLease` and `SoftFileLock` are locked out of the path permanently, and the docs still describe the old behavior (executed on head; base result inferred).**
- **Location:** the sentinel at `_strict.py:247-270` is never removed. The stale docs are `docs/how-to.rst:625-675` ("Choose a soft-lock contract"), which is not part of the diff, and `docs/changelog/636.feature.rst`.
  - The how-to section still says strict "never reclaims a marker" and points to `MarkerSoftFileLock.force_break`. StrictSoftFileLock is no longer a subclass of `MarkerSoftFileLock`, and its `force_break` now requires a claim name.
  - Its table says "SoftFileLock with StrictSoftFileLock: legacy evicts the protocol 2 marker" and "the lease waits out a strict holder".
  - The 636 changelog entry still describes the marker design.
- **Trigger:** `with StrictSoftFileLock(p): pass`, then `SoftFileLease(p, lease_duration=.2, timeout=1).acquire()`. `SoftFileLease._try_break_stale_lock` reads the sentinel as an unparsable record, so it never breaks it.
- **Head:** both `SoftFileLease` and `SoftFileLock` raise Timeout although no one holds the lock.
- **Base:** inferred, not observed. The first run of `p1_lease_after_strict.py` printed "acquired" for both classes, but that came from the base checkout with head code still loading from an installed filelock. After that was fixed, the base run gave the same result as head (both Timeout, sentinel exists). The base strict lock unlinks its marker on release, so base behavior needs a clean base-only interpreter to settle.
- **Contract broken:** the how-to compatibility table. The new `concepts.rst` text names only "legacy clients", and `SoftFileLease` is a new 3.30 class.
- **Your decision:** either the docs and changelog are wrong, or the lease lock-out is unintended.
- **Probe:** `p1_lease_after_strict.py`, output `p1.out`.

**C4. `release()` on a shared instance that is not held blocks while another thread waits in `acquire()` (executed).**
- **Location:** `src/filelock/_api.py:1121-1122`. `release()` takes `_transition_lock` with no timeout, and `_transition_admission` holds that lock for the whole poll wait.
- **Trigger:**
  1. Create the lock with `thread_local=False`.
  2. Thread A calls `acquire(timeout=2)` while another instance holds the lock.
  3. The main thread calls `shared.release()`.
- **Head:** `release()` returned after 1.82s. With `timeout=-1` it would never return.
- **Base:** returned after 0.00s.
- **Contract broken:** `release()` of a lock that is not held is a no-op that does not wait. A shutdown or cleanup thread can hang.
- **Probe:** `p3_release_blocks_on_gate.py`, output `p3.out`.

**C5. The lifetime warning gives the wrong reason for StrictSoftFileLock (executed, minor).**
- **Location:** `_strict.py:74`. The class now subclasses `BaseFileLock` and does not set `_lifetime_unsupported_reason`.
- **Trigger:** `StrictSoftFileLock(p, lifetime=5)`.
- **Head:** "lifetime is ignored for StrictSoftFileLock: a native OS lock cannot be broken safely by file age".
- **Base:** "...: a strict lock never reclaims a marker by age".
- **Probe:** `p6_api_surface.py`, output `p6.out`.

## Dropped leads
- **Async strict has no jittered backoff** (`_async_poll_until_acquired` never calls `_poll_delay`). On Linux, 8 processes × 200 async acquisitions at a 0.5 ms poll finished in 1.9s with 0 timeouts (`p4_async_stress.py`, `p4.out`). It could matter on Windows only, which I could not check.
- **Claims leaked when a directory descriptor fails to close after publication or linking** (lines 133-135 and 154-156). The head tests `test_strict_soft_held_directory_close_failure_leaves_both_claims` and `..._private_close_failure_leaves_public_claim` assert this leak as intended fail-closed behavior.
- **Mutual exclusion between two doorways.** I traced the interleavings of the intent and held scans with the minimum-token rule. Held claims persist and the final check covers every claim, so I found no overlap; the 8-process sync stress passed.
- **Public API removed** (`owner`, `pid`, `is_lock_held_by_us`, and `force_break()` without arguments; `p6.out`). StrictSoftFileLock was added in 3.30.0, which is unreleased (changelogs 636 and 637 are both unreleased).
- **Async locks never get `_transition_lock`.** Every path that uses it (sync `acquire`, `release`, `__del__`) is overridden by `BaseAsyncFileLock`, and `_reset_after_fork_in_child` only assigns it.
- **`claim_root` survives on a successful sync acquisition.** It is cleared in `_release`, in `_reconcile_failed_acquire`, and in the fork reset.
- **Legacy clients breaking the sentinel.** It parses as pid 1 on a host that never matches, so old and new `SoftFileLock` both leave it alone. Removal by `lifetime` or `break_lock()` is documented as voiding exclusion.
- **Unknown file names or unreadable claims raise a protocol error.** This is the documented fail-closed design.
- **A non-blocking acquire gets Timeout while another thread holds the admission gate briefly.** This race also exists at base, and the outcome is equivalent.
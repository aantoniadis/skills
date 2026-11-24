I read the whole diff once and ran 7 probes. Six candidates survived. In P1, P2, P3, P6 and P7 the source left the outcome open, so I ran them; the docs candidate is backed by P4. I compared base and head wherever the base has an equivalent path. The checkout is unchanged: I worked from `git archive` exports of base and head (with `version.py` copied in) under `finder-general/{base,head}`.

All paths below are relative to `<scratch>/out-arm/find-bugs-filelock-1/.scratch/strict-owner-claims/search-1/finder-general/probes/`. Each `pN_*.py` has a log next to it, `pN.{base,head}.log`, whose first line is the exact command. The general form is `PYTHONPATH=<base|head>/src /tmp/real-pr-cache/filelock/venv/bin/python probes/pN_*.py`, run from `finder-general/`.

## Candidates

**1. A failed doorway cleanup leaves the instance "locked", and the next `acquire()` succeeds while a competitor holds the lock (executed).**
- **Location:** `src/filelock/_strict.py` `_discard_doorway` (lines 211–216), which marks the sentinel as owned when any owner path remains. Together with `_rollback_failed_acquire` (181–188) and the base `_reconcile_failed_acquire`, this leaves `lock_counter=1` and `is_locked=True`.
- **Trigger:**
  - The final rescan sees a competitor with a smaller token, so the doorway discards.
  - Unlinking our intent fails, for example a transient EACCES. Unlinking our held claim succeeds.
  - The first `acquire()` raises. A retry `acquire(timeout=0)` then returns as a reentrant success.
- **Head result:** the first acquire raises PermissionError and leaves `is_locked=True`, counter 1. On disk are the competitor's `held-v1-000…` and our `intent-v1-fff…`; we have no held claim. The retry succeeds with counter 2, while a fresh contender gets Timeout.
- **Base result:** this doorway does not exist in the base (the base class is the marker-based lock), so there is no base comparison.
- **Contract broken:** mutual exclusion ("no peer enters while this holder lives"). The repo's own test `test_strict_soft_doorway_preserves_every_claim_cleanup_error` asserts `is_locked=True` with a competitor's held claim present, but nothing guards a re-acquire.
- **Probe:** `p1_failed_doorway_reacquire.py`, log `p1.head.log`.

**2. Shared-instance `release()` of an unheld lock blocks behind another thread's whole blocking `acquire()` (executed).**
- **Location:** `src/filelock/_api.py` `release()`, around lines 1121–1122. The `_transition_lock` is taken before the `not self.is_locked` early return, and `_transition_admission` holds the gate for the entire poll loop.
- **Trigger:** a `StrictSoftFileLock(thread_local=False)` instance. Thread A is in `acquire(timeout=2)` while another process holds the lock. Thread B calls `shared.release()`.
- **Base result:** `release()` returns in 0.00s.
- **Head result:** `release()` takes 1.72s and returns only after A times out. With `timeout=-1` it would block indefinitely.
- **Contract broken:** `release()` on an unheld lock is a no-op that returns immediately.
- **Probe:** `p3_release_blocks_on_gate.py`, logs `p3.base.log` and `p3.head.log`.

**3. Jittered backoff never jitters at the default `poll_interval`, and async never backs off at all (executed).**
- **Location:** `src/filelock/_api.py` `_poll_delay`. The cap `_poll_backoff_cap = 0.05` equals the default `poll_interval = 0.05`, so `max(poll_interval, rand(0..0.05))` is always 0.05. Separately, `BaseAsyncFileLock._async_poll_until_acquired` sleeps the fixed `poll_interval` and never calls `_poll_delay`.
- **Trigger:** the default `poll_interval` (or any value ≥ 0.05), or any `AsyncStrictSoftFileLock`.
- **Head result:** at 0.05 and 0.1 there is exactly 1 distinct delay value; at 0.0005 there are 981. The async loop does not use `_poll_delay`.
- **Contract broken:** commit b072b3b says contending processes "desynchronize instead of livelocking". That only happens for sync locks with `poll_interval < 0.05`.
- **Limit:** a 6-process × 2-thread stress run on Linux showed no livelock and no overlap at either 0.0005 or 0.05 (`p5_stress_exclusion.py`, `p5.head.log`). The impact is unproven on Linux; the commit reported the livelock on Windows.
- **Probe:** `p2_jitter_default.py`, log `p2.head.log`.

**4. Two users can no longer share one strict lock path (executed).**
- **Location:** `src/filelock/_strict.py` `_ensure_protocol_directory` (lines 773–775). It runs `directory.mkdir()` with the default mode, so under umask 022 the directories come out 0755 and owned by the first user. The `mode` argument is applied only to records, never to `<lock>.filelock` or `claims/`.
- **Trigger:** a world-writable sticky directory, like `/tmp`. User 1001 runs `StrictSoftFileLock(path, mode=0o666)` and acquires then releases; user 1002 then acquires.
- **Base result:** both users acquire.
- **Head result:** user 1002 gets `PermissionError: [Errno 13] … .intent-v1-….private-v1-….tmp`. Both protocol directories are `0o40755`, owned by uid 1001.
- **Contract broken:** shared-path locking that the base supported and `mode=0o666` asks for. The error is raw `PermissionError` rather than a protocol error, and it surfaces on every later acquire by other users.
- **Probe:** `p7_multi_user.py`, run as root with children that setuid; logs `p7.base.log` and `p7.head.log`.

**5. A filesystem without hard links raises `PermissionError` instead of `SoftFileLockProtocolError` (executed with a mock).**
- **Location:** `src/filelock/_strict.py` `_raise_if_hard_links_unsupported` (lines 799–807), which maps only ENOSYS, ENOTSUP and EXDEV. Linux `link(2)` returns EPERM when "the filesystem … does not support the creation of hard links" (vfat/exfat).
- **Trigger:** `os.link` fails with EPERM during sentinel publication.
- **Head result:** ENOTSUP gives `SoftFileLockProtocolError` as expected, but EPERM gives `PermissionError: [Errno 1]`.
- **Contract broken:** `docs/how-to.rst` says "If hard-link publication is unavailable, acquisition raises SoftFileLockProtocolError".
- **Limit:** I simulated EPERM by patching `os.link`; I could not mount a real vfat filesystem.
- **Probe:** `p6_link_eperm.py`, log `p6.head.log`.

**6. The "Choose a soft-lock contract" docs section is now false (executed).**
- **Location:** `docs/how-to.rst` lines 625–675, which this change did not update.
- **What the docs still say:**
  - Strict "never reclaims a marker".
  - Recovery goes through `MarkerSoftFileLock.force_break()`.
  - Both classes publish a protocol-2 record.
  - In the table, a `SoftFileLock` contender "evicts" a strict marker, and a lease "waits out a strict holder".
- **What head actually does:**
  - `StrictSoftFileLock` is no longer a `MarkerSoftFileLock`.
  - `force_break()` without an argument raises TypeError (it now requires `claim_name`).
  - `SoftFileLock` and `SoftFileLease` are blocked both during and after strict holds, because the sentinel is permanent.
- **Base result:** the text matched the base class.
- **Probe:** `p4_mixed_contracts_vs_docs.py`, logs `p4.base.log` and `p4.head.log`. Incidentally, `p4.base.log` shows that at base a `SoftFileLease` overlapped a strict holder; that is a base issue, not part of this change.

## Dropped leads
- **Safety of the doorway order (bakery-style):** I traced every interleaving of the scan, intent, rescan, link held and final rescan steps; the winner's held claim stays visible to any later publisher. The `p5` stress run found 0 overlaps.
- **Sync `claim_root` not cleared after a successful acquire:** it is cleared in `_release`, in `_reconcile_failed_acquire` when unlocked, and on fork. The async path clears it in `finally`. It is only read during polling.
- **`SoftFileLockProtocolError` subclassing OSError with a custom `__init__`:** OSError defers argument parsing to the overridden `__init__`, and pickling is handled by `__reduce__` and tested.
- **Lifetime expiry deleting the sentinel:** `_lifetime_supported` defaults to False in `BaseFileLock`, and strict does not override it.
- **The `SoftFileLock` sentinel-equality check:** harmless and effectively redundant, since the sentinel's hostname never matches a real host.
- **Explicit `mode` not enforced with fchmod:** `SoftFileLock` behaves the same, so this is not a regression.
- **tox `3.14` env calling `uv` without `allowlist_externals`:** CI installs tox with tox-uv, and the commit history shows that env ran. I could not check further without network.
- **Async `_transition_lock` missing from `BaseAsyncFileLock.__init__`:** async overrides `acquire`, `release` and `__del__`, so the sync gate is never touched there.
- **`_unlink_owner_path(intent_path)` return value ignored after a win:** it only drops an `os.close` error on the directory descriptor, and the claim itself was removed.
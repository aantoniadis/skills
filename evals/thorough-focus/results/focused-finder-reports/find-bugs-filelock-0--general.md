This was one read of 126cab7..e6538e1, done alone with no workers. It produced six candidates I could not contradict. Five were run at both base and head. The documentation one is partly inferred: only part of it was run.

The checkout is unchanged. My work is in `<scratch>/out-arm/find-bugs-filelock-0/.scratch/strict-owner-claims/search-1/finder-general/`, which holds the worktrees `base/` and `head/` and the folder `probes/`. Probe scripts, outputs and exact commands are in `probes/`, with the commands in `probes/COMMANDS.md`. Every probe prints `filelock.__file__`, and each run loaded the intended worktree.

## Candidates

**1. The strict lock never jitters its retries at the default `poll_interval`**
- **Location:** `src/filelock/_api.py` `_poll_delay` (`window = min(cap, ...)`, `return max(poll_interval, randbelow(window))`), with `_strict.py:83` `_poll_backoff_cap = 0.05`.
- **Trigger:** the default `poll_interval=0.05`, or any value of 0.05 or more. The cap equals the default interval, so `max(poll_interval, random ≤ cap)` always returns `poll_interval`.
- **Base:** no backoff existed.
- **Head:** across 3,980 samples at 0.05 and at 0.1 there was one distinct delay, the interval itself. Only a value below 0.05 produced jitter: 0.01 gave 3,083 distinct delays.
- **Contract broken:** commit b072b3b and the comments at `_strict.py:81-82` and `_api.py` `_poll_backoff_cap` say contending processes "desynchronize instead of livelocking". At default settings they still retry in lockstep. The async path, `asyncio._async_poll_until_acquired`, never calls `_poll_delay` at all. No test covers `_poll_delay`.
- **Probe:** `probes/p1_backoff_default.py` (executed at head only, since base has no such code).

**2. Users who share a lock with `mode=0o666` can no longer share a strict lock**
- **Location:** `_strict.py:93-95`. `_ensure_protocol_directory` calls `directory.mkdir()` with the default mode and the umask, and ignores the lock's `mode`.
- **Trigger:** two OS users, umask 022, a shared directory with mode 1777, and `StrictSoftFileLock(p, mode=0o666)`. User A acquires and releases, then user B acquires.
- **Base:** both users acquire and release.
- **Head:** user B gets `PermissionError: [Errno 13] ... '.intent-v1-....claim.private-v1-....tmp'`. `work.lock.filelock/` and `claims/` are created 0755 and owned by A. The sentinel is 0644 even though `mode=0o666` was passed.
- **Contract broken:** `mode` exists so one lock can be shared across users. The base strict lock supported this; the head blocks every other user for good, because the directories are permanent.
- **Probe:** `probes/p2_multiuser.py` (executed). It needs readable copies of the sources at `/tmp/fl-probe-{base,head}-src` so uids 1000 and 1001 can traverse to them.

**3. On a shared instance, `release()` blocks behind another thread's pending acquire**
- **Location:** `_api.py` `release()`, at `with self._transition_lock if serialize ...`. `_transition_admission` holds that RLock for the whole of `_poll_until_acquired`, waiting included.
- **Trigger:** `StrictSoftFileLock(p, thread_local=False)`. Thread T1 waits in `acquire(timeout=3)` while another instance holds the path. Thread T2 calls `shared.release()` on the unheld instance.
- **Base:** returns in 0.00s.
- **Head:** takes 2.74s. With `timeout=-1` it would block until T1 acquires.
- **Contract broken:** before the change, releasing an unheld lock was an immediate no-op. The `is_locked` and creator-PID early return now runs inside the gate.
- **Probe:** `probes/p4_shared_release_blocks.py` (executed).

**4. A lock path that can never be a lock now times out instead of raising**
- **Location:** `_strict.py:247-253` `_open_or_create_sentinel`. Every `OSError` from `_open_sentinel` other than `FileNotFoundError` returns `None`, which reads as contention. `_open_record` raises a plain `OSError` for anything that is not a regular file.
- **Trigger:** the lock path is an existing directory. The source shows the same handling for a symlink or an unreadable sentinel, but I did not run those cases.
- **Base:** `IsADirectoryError` after 0.00s.
- **Head:** `Timeout` after 1.01s. With the default `timeout=-1` it would hang forever.
- **Contract broken:** a configuration error is hidden as contention. Base raised; the docs promise a `SoftFileLockProtocolError` for damaged protocol state.
- **Probe:** `probes/p5_bad_lock_path.py` (executed).

**5. The docs and changelog still describe the old marker-based strict lock (partly inferred)**
- **Location:** `docs/how-to.rst` "Choose a soft-lock contract", head lines 623-675, is unchanged. It says strict publishes a protocol 2 marker and points to `MarkerSoftFileLock.force_break` with no argument. Its table says `SoftFileLock` evicts a strict marker and that "the lease waits out a strict holder". `docs/changelog/636.feature.rst` still announces the marker-based `StrictSoftFileLock` next to the new `637.feature.rst`.
- **Base and head:** after one strict hold and release, base lets both `SoftFileLease` and `SoftFileLock` acquire. Head leaves `work.lock` and `work.lock.filelock`, and both time out. This matches the new concepts.rst text, but contradicts the how-to table.
- **Contract broken:** the documentation.
- **Probe:** `probes/p3_lease_after_strict.py` (executed). The changelog part is inferred from the source.

**6. The lifetime warning gives the wrong reason (minor)**
- **Location:** `_strict.py` `StrictSoftFileLock` no longer sets `_lifetime_unsupported_reason`, so it inherits the native-lock text.
- **Trigger:** `StrictSoftFileLock(p, lifetime=5)`.
- **Base:** "a strict lock never reclaims a marker by age".
- **Head:** "a native OS lock cannot be broken safely by file age". `lifetime` is still dropped to `None`.
- **Contract broken:** the warning message.
- **Probe:** `probes/p6_lifetime_warning.py` (executed).

## Dropped leads
- **A failed directory close leaves orphan intent or held claims** (`_attempt_doorway` raises `publication_cleanup_error` before recording the path, and resets `owner_claim_paths = ()` on `link_cleanup_error`). Intended: `test_strict_soft_private_close_failure_leaves_public_claim` and `test_strict_soft_held_directory_close_failure_leaves_both_claims` assert that the claims stay, by fail-closed design.
- **Two holders through the doorway.** I reasoned through each ordering of intent, scan, link and rescan for two tokens. The step-3 check for a held claim, combined with the step-5 lowest-token check, admits at most one holder under coherent directory reads.
- **Private-record reclamation racing the publisher.** `_link_private_record` checks the public name's identity, and a reclaim before the link causes a retry rather than an entry.
- **The `claim_root` reset in the async `finally` after success.** `_claim_directory` uses `owner_claim_paths` while held, and `_release` resets it anyway.
- **The fork child inheriting the transition lock or claim paths.** `_reset_after_fork_in_child` resets all three.
- **The `StrictSoftFileLock` API break against the base** (`owner`, `pid`, `force_break()` with no argument). The base's marker version appears unreleased: installed filelock 3.30.2 already ships the claim-based class.
- **The `SoftFileLock` sentinel skip.** Intended and documented in the new concepts.rst. `SoftFileLease` also never breaks the sentinel, because `parse_marker` returns `None` for it.
- **Thread-local `claim_root` on async locks.** `asyncio.py:93` rejects `thread_local` combined with `run_in_executor`.
- **The tox `[env."3.14"]` `set_env` override.** It restores `COVERAGE_FILE`, and `env_run_base` has no other `set_env` or `commands_pre` to lose.
- **Head strict test failure** `test_strict_soft_unreadable_claim_fails_closed`. Environmental: root can read a mode-000 file.
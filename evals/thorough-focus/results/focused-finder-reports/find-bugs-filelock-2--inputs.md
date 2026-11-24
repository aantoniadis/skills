I found six candidates I could not contradict, five of them from probes run on both base and head. This was one read of the change, and I started no workers.

The probes and logs are in `<scratch>/out-arm/find-bugs-filelock-2/.scratch/strict-owner-claims/search-1/finder-inputs/`. That folder holds the scripts `p1_multiuser_mode.py`, `p2_malformed_paths.py`, `p3_release_blocks.py` and `p5_hostname_namelen.py`, the output in `run1.log` and `run2.log`, and the exact commands in `COMMANDS.txt`. Every probe ran with Python 3.13 from the venv, as root, with `PYTHONPATH=wt-{base,head}/src`. The checkout is unchanged.

## Candidates

**1. A second user can no longer use a shared lock after the first user's acquire** (executed, `p1_multiuser_mode.py`, `run1.log`)
- **Location:** `src/filelock/_strict.py:93-95` (`_ensure_protocol_directory` calls `directory.mkdir()` with no mode) and `:433-436`, where the private record is created inside `claims/`.
- **Trigger:** the lock is in a world-writable sticky directory such as `/tmp`, with `mode=0o666`. User A (root) acquires and releases. Then user B (`nobody`) acquires. The default `mode` should fail the same way, because the directories come from umask either way; I did not run that case.
- **Base:** B acquires. Nothing is left behind after A releases.
- **Head:** A leaves `work.lock` and `work.lock.filelock/claims`, both `0o40755` and owned by A. B gets `PermissionError [Errno 13] ... '.intent-v1-....claim.private-v1-....tmp'`, and it will keep failing because the directories are permanent.
- **Contract broken:** the documented `mode` and default-ACL behaviour for shared directories (`docs/concepts.rst` "File permissions and mode"). The lock stops working across UIDs. `mode` reaches only the record files, never the coordination directories.

**2. A lock path that is a directory now times out instead of raising** (executed, `p2_malformed_paths.py`, `run1.log`)
- **Location:** `_strict.py:247-253, 273-278`. `_open_or_create_sentinel` turns any `OSError` other than `FileNotFoundError` from `_open_sentinel`, including "is not a regular file", into `None`, which reads as contention.
- **Trigger:** `StrictSoftFileLock(<existing directory>)`.
- **Base:** `IsADirectoryError` after 0.00s, with nothing created.
- **Head:** `Timeout` after 1.01s with `timeout=1`, and it creates `isdir.filelock/` as litter.
- **Consequence:** with the default `timeout=-1` the call waits forever, and the cause is never reported. The same code path also hides permission and other open errors on an existing sentinel.

**3. `release()` on an unlocked shared instance blocks while another thread is waiting in `acquire()`** (executed, `p3_release_blocks.py`, `run1.log`)
- **Location:** `src/filelock/_api.py:1119-1123`. `release` takes `_transition_lock` before the `not self.is_locked` early return, and `acquire` holds that lock (`_api.py:1057`, `_transition_admission`) for its whole poll loop.
- **Trigger:** a `thread_local=False` strict lock. Thread A calls `acquire(timeout=3)` on a path another instance holds. Thread B calls `release()`.
- **Base:** returns in 0.00s.
- **Head:** returns only after 2.74s, when A's acquire timed out. With `timeout=-1` it blocks indefinitely.
- **Contract broken:** `release()` on an unheld lock has always been an immediate no-op. Async checks `is_locked` before taking its gate (`asyncio.py:462-464`), so async is not affected.

**4. Lock basenames of 207 to 255 characters now fail** (executed, `p5_hostname_namelen.py`, `run2.log`)
- **Location:** `_strict.py:519-520` (the private sentinel name is `.` + basename + `.private-v1-` + 32 hex characters + `.tmp`, so 49 extra characters) and `:91` (`<basename>.filelock`, so 9 extra characters).
- **Trigger:** a basename of length 207 or more.
- **Base:** acquires at lengths 200, 206, 207, 240, 246, 247 and 255.
- **Head:** acquires at 200 and 206. From 207 to 246 it fails with `OSError [Errno 36] File name too long: '.aaaa…'`. At 247 and 255 it fails on the `.filelock` directory.
- **Contract broken:** any path the filesystem accepts used to work. Nothing in the docs mentions the new limit.

**5. A hostname containing whitespace makes the lock unusable, even for its own claims** (executed by monkeypatching `socket.gethostname`, `p5_hostname_namelen.py`, `run2.log`)
- **Location:** `_strict.py:367-369`. `_parse_claim` rejects a hostname that is not printable or contains whitespace, but `_claim_record` (`:395-397`) writes whatever `gethostname()` returns.
- **Trigger:** a hostname such as `"my host"` or `"tab\there"`. Linux `sethostname` accepts these.
- **Base:** acquires.
- **Head:** `SoftFileLockProtocolError ... claim 'intent-v1-….claim': malformed claim record` on every acquire. Contenders on other hosts would fail the same way while such a claim exists.
- **Contract broken:** the writer and the parser disagree, so the lock is permanently unusable on such a host. An empty hostname and a non-ASCII one (`höst`) still work.

**6. The backoff jitter does nothing at the default `poll_interval`** (executed in `p3_release_blocks.py`, head only, since the code is new)
- **Location:** `_api.py:1238-1247` together with `_strict.py:83` (`_poll_backoff_cap = 0.05`). The default `poll_interval` is also 0.05 (`_api.py:349`).
- **Trigger:** the default `poll_interval`.
- **Result:** `window = min(0.05, …) = 0.05`, and the function returns `max(0.05, rand ≤ 0.05)`, which is always 0.05. Over 199 attempts there was 1 distinct delay at 0.05, against 133 at `poll_interval=0.01`.
- **Contract broken:** the code comment says contending processes back off across a jittered window so they desynchronize instead of livelocking. That never happens with defaults, and every contender polls in lockstep. The async poll loop (`asyncio.py:372-373`) never calls `_poll_delay` at all.
- **Note:** this is a liveness concern only. I did not show an actual livelock.

## Minor
- **Wrong reason in the lifetime warning** (executed, `run1.log`). `StrictSoftFileLock(..., lifetime=5)` on head warns "a native OS lock cannot be broken safely by file age". On base it said "a strict lock never reclaims a marker by age". The class no longer sets `_lifetime_unsupported_reason`, so it inherits the reason meant for native locks, which misdescribes this soft lock.

## Dropped leads
- **Existing empty or foreign file at the lock path:** base and head both time out (`run1.log`). Head only adds `.filelock` litter.
- **`on_acquired` rejected:** base rejects it too, with the same `ValueError`.
- **`force_break()` now requires `claim_name`:** base's strict class is unreleased (the `637` changelog fragment is pending and both versions say `versionadded 3.30.0`), and the change is documented.
- **No hard-link support raises `SoftFileLockProtocolError`:** this is documented intent.
- **Two contenders both entering the doorway:** I traced the intent, held and rescan ordering. A winner with the smaller token must have published its intent after the other's rescan, so it then sees that holder's held claim and backs off. The only outcome is mutual back-off, which is a liveness issue and covered by candidate 6.
- **Odd `poll_interval` values:** 0, negative, `inf` and `nan` give the same result through `_poll_delay` as through base's `sleep`: a ValueError for negative and `nan`, a zero or infinite sleep otherwise.
- **`claim_root` reset in async `finally` even on success:** release uses `owner_claim_paths`, not `claim_root`, so nothing changes.
- **`blocking=False` or `timeout=0` at the gate:** both raise `Timeout` immediately, consistent with polling.
- **Another `MarkerSoftFileLock` evicting the sentinel:** mixing lock classes on one path is outside the documented contract.
- **Lock in a read-only directory:** I did not run it, because root bypasses permissions. Both versions raise `PermissionError` from create or `mkdir` by source.
- **Windows and macOS branches** (`_unlink_relative` win32, `_link_no_replace` without dir_fd, delete-pending retry): not probed on Linux. These are open, not contradicted.
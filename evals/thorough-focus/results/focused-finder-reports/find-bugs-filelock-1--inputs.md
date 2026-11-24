I found six candidates I could not contradict and dropped five leads. This was one read. I started no workers and did not run the static deltas, `weakened_checks.py` or the base tests, since you said you would run those.

**Setup.** Base `126cab7` and head `e6538e1` are checked out as worktrees under `<scratch>/out-arm/find-bugs-filelock-1/.scratch/strict-owner-claims/search-1/finder-inputs/{base,head}`, each with `version.py` copied in. Probes ran on Python 3.13, Linux, ext4 `/tmp`, as root. Scripts, outputs and `COMMANDS.txt` are in `.../finder-inputs/probes/`. The reviewed checkout is unchanged (`git status` is clean). Running the probes wrote `__pycache__` folders into my own worktrees only.

## Candidates

**1. Two OS users sharing one lock path: the second user can never acquire (executed, `p2_crossuser.py` / `.out`)**
- **Location:** `src/filelock/_strict.py`, `_ensure_protocol_directory` and `_publish_record`. Head also leaves a permanent sentinel at `<path>` (`_open_or_create_sentinel`).
- **Trigger:** `/tmp`-style folder (mode 1777). Root with umask 022 acquires and releases `StrictSoftFileLock(p, mode=0o666)`. Then user `nobody` tries to acquire.
- **Base:** both users print `acquired and released`.
- **Head:** `nobody` gets `PermissionError [Errno 13] ... '.intent-v1-....claim.private-v1-....tmp'`, and so does every later attempt. The `<path>.filelock/claims` folders are created by `mkdir` with umask modes (`drwxr-xr-x root`) and `mode=` never applies to them.
- **Inferred variant:** with umask 077 the sentinel itself is `0600`. `_open_sentinel` then raises `PermissionError`, which `_open_or_create_sentinel` turns into `None`. The second user then waits silently until timeout, or forever with `timeout=-1`.
- **Contract broken:** the `mode` option and multi-user use of a shared lock folder worked at base. The protocol state now outlives release and is owned by the first user.

**2. Lock path that is a folder: immediate error becomes a timeout or a permanent hang (executed, `p1_paths.py` / `.out`, "directory")**
- **Location:** `_strict.py`, `_open_or_create_sentinel`. Its `except OSError: return None` treats a non-regular file at the lock path as "not acquired".
- **Base:** `IsADirectoryError` after 0.00 s.
- **Head:** `Timeout` after 0.51 s with `timeout=0.5`, and a stray `dir.lock.filelock/` folder is created. With the default `timeout=-1` it hangs forever.
- **Contract broken:** a misconfiguration that base reported now looks like contention. The same path makes an unreadable or `EACCES` sentinel invisible (see candidate 1's variant).

**3. `release()` on a shared instance blocks, then releases another thread's new acquisition (executed, `p3_shared_release.py` / `.out`)**
- **Location:** `src/filelock/_api.py`, `BaseFileLock.release`, which now takes `with self._transition_lock`. `_transition_admission` holds that gate for the whole blocking wait in `_poll_until_acquired`.
- **Trigger:** `StrictSoftFileLock(p, thread_local=False)` shared by two threads. Thread A waits in `acquire(timeout=2)` while another holder has the path. The main thread calls `X.release()` while X is not held.
- **Base:** `release()` returns in 0.00 s as a no-op. A acquires, and `X.is_locked` is `True`.
- **Head:** `release()` blocks 0.51 s until A acquires, then releases A's lock. A's `acquire()` returned success, but `X.is_locked` is `False`, so A runs its critical section unprotected. With `timeout=-1` the release blocks for as long as A waits.
- **Contract broken:** releasing an unheld lock is a no-op, and a successful `acquire()` means the lock is held.

**4. Lock basenames of 207–255 characters now fail with `ENAMETOOLONG` (executed, `p6_long_name.py` / `.out`)**
- **Location:** `_strict.py`, `_private_record_name`, which adds 49 characters to the basename (`.` + `.private-v1-` + 32 hex + `.tmp`), and the `.filelock` suffix on the coordination folder.
- **Base:** every length up to 250 acquires.
- **Head:** `OSError [Errno 36] File name too long` from length 207 on. From 247 on it fails at the coordination folder.
- **Contract broken:** any lock name the filesystem accepts used to work. This is a boundary case of limited reach.

**5. `lifetime=` warning gives the wrong reason (executed, `p1_paths.py` / `.out`, "lifetime")**
- **Location:** `StrictSoftFileLock` now subclasses `BaseFileLock` and inherits `_lifetime_unsupported_reason = "a native OS lock cannot be broken safely by file age"`.
- **Base:** "a strict lock never reclaims a marker by age".
- **Head:** the warning calls the strict soft lock a native OS lock. Cosmetic.

**6. Stale documentation in `docs/how-to.rst`, "Choose a soft-lock contract" (executed, `p5_mixed.py` / `.out`)**
- **Location:** around lines 625–676, a section the diff did not touch.
- **What it still says:** strict publishes a "protocol 2 record", and recovery is via `MarkerSoftFileLock.force_break` with no argument. Its table says "StrictSoftFileLock with SoftFileLease: the lease waits out a strict holder" and "SoftFileLock ... evicts the protocol 2 marker".
- **Head behaviour:** after one strict acquire and release, `SoftFileLease` and `SoftFileLock` both time out permanently because the sentinel stays. `force_break()` raises `TypeError: missing 1 required positional argument: 'claim_name'`. This contradicts the new `concepts.rst` and how-to text.
- **Base behaviour:** both acquire, and `force_break()` succeeds.

## Dropped leads
- **No backoff in the async poll loop (livelock):** `p4_contention.out` shows 8 processes × 40 cycles with zero timeouts. Head async took 0.97 s against base 0.90 s.
- **API break (`force_break` signature, `owner`, base class):** the base `StrictSoftFileLock` is unreleased (changelog fragment 636 is pending for 3.30.0).
- **Symlink, dangling symlink or empty file at the lock path:** base and head both time out (`p1`).
- **Fork with a held gate or claims:** `_reset_after_fork_in_child` resets `_transition_lock`, `owner_claim_paths` and `claim_root`.
- **Async objects lacking `_transition_lock`:** async `acquire`/`release` never touch it (they use `_transition_gate`), and the sync gate only applies to subclasses with `_serialize_transitions=True`.

## Not probed (inferred, minor)
- **Backoff can overshoot the timeout:** `_poll_delay` can sleep up to `_poll_backoff_cap` (0.05 s) beyond `poll_interval`, so `acquire(timeout=0.01, poll_interval=0.001)` with the path held may return `Timeout` up to about 50 ms late. Probe: time that call on base and head.
- **Filesystem side effect on import:** `import filelock` now creates and deletes a temporary folder at import time (`_probe_link_follow_symlinks`). Probe: `strace -f -e trace=mkdir,link python -c 'import filelock'` on base and head.
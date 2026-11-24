I made the listed failure points fail and probed what another process or account could leave at each path. There are six candidates I could not contradict, five of them confirmed by base/head probes. The checkout is unchanged, and the base and head worktrees are in my folder.

F = `<scratch>/out-arm/find-bugs-filelock-0/.scratch/strict-owner-claims/search-1/finder-faults`. Probes and outputs are in `F/probes/`, with the exact commands in `F/probes/COMMANDS.txt`. Every run prints `filelock.__file__` to confirm it loaded the intended checkout. I ran as root and used `setpriv` to act as uids 1000 and 1001. The cross-account probes used temporary directories under `/tmp/fl-finder-faults-p*`, which they delete when done.

## Candidates

**1. A second account can never acquire a lock path another account has used** (executed: `p1_two_accounts.sh`, also `p3_claims_unsearchable.sh`)
- **Location:** `src/filelock/_strict.py:94-95` (`_ensure_protocol_directory` calls `directory.mkdir()`). The directories get umask permissions and ignore the lock's `mode`. Account B's first failing call is the open of its private claim record at `:436` / `:601`.
- **Trigger:** two accounts lock the same path in a shared sticky 1777 directory with umask 022. uid 1000 acquires and releases, then uid 1001 tries.
- **Base:** both accounts acquire.
- **Head:** uid 1001 gets `PermissionError: [Errno 13] ... '.intent-v1-....claim.private-v1-....tmp'`. `resource.lock.filelock/claims` is permanently `drwxr-xr-x` and owned by uid 1000.
- **Umask 077 variant (p3):** `lock.claims` and `acquire()` from the other account raise a plain `PermissionError`, not the documented `SoftFileLockProtocolError` for unreadable claims.
- **Contract:** base handled shared-directory use across accounts. The docs say an explicit `mode` is applied, but it does not reach the new directories.

**2. Acquisition fails when the lock's parent directory is writable but not readable** (executed: `p2_unreadable_parent.sh`)
- **Location:** `_strict.py:538`, where `_reclaim_sentinel_private_records` calls `os.scandir(path.parent)` (reached from `:255` when the sentinel does not exist yet).
- **Trigger:** a parent directory with mode 1733, owned by root; uid 1000 acquires.
- **Base:** acquired.
- **Head:** `PermissionError: [Errno 13] Permission denied: '<parent>'`. It also leaves behind the `.filelock/claims` directories it had already created.
- **Contract:** base handled this directory. Listing the whole parent directory is a new requirement.

**3. A private sentinel record orphaned by a crash is never reclaimed** (executed: `p4_sentinel_private_orphan.py`, head only; base has no private records)
- **Location:** `_strict.py:255`. Sentinel-private reclamation only runs when the sentinel is missing, and the sentinel is permanent once published.
- **Trigger:** a process dies after linking the sentinel but before unlinking `.resource.lock.private-v1-<hex>.tmp`. Others then acquire three times after waiting more than 2 s.
- **Head:** the private record is still in the user's directory after all three acquisitions. The same holds for a crash before the link once anyone else creates the sentinel.
- **Contract:** `docs/concepts.rst` and `docs/how-to.rst` say linked private names are discarded immediately and abandoned ones are reclaimed after two seconds.

**4. A filesystem without hard links raises `PermissionError` instead of the documented `SoftFileLockProtocolError`** (executed: `p5_link_eperm.py`; `os.link` is replaced to raise EPERM because no vfat driver is available here)
- **Location:** `_strict.py:799-807`. `_raise_if_hard_links_unsupported` only maps ENOSYS, ENOTSUP and EXDEV, but Linux link(2) returns EPERM when the filesystem cannot create hard links (e.g. vfat).
- **Base:** acquired.
- **Head:** raw `PermissionError: [Errno 1]`, leaving `resource.lock.filelock` behind.
- **Contract:** how-to says "If hard-link publication is unavailable, acquisition raises SoftFileLockProtocolError".

**5. Lock basenames longer than about 206 bytes now fail with ENAMETOOLONG** (executed: `p7_long_name.py`)
- **Location:** `_strict.py:91` (`<name>.filelock`) and `:520`. The private name `.<name>.private-v1-<32hex>.tmp` adds 49 bytes to the basename.
- **Base:** basenames of 200, 210, 240 and 250 bytes all acquire.
- **Head:** 200 acquires; 210, 240 and 250 raise `OSError` errno 36.
- **Contract:** base handled any name the filesystem accepts.

**6. A directory at the lock path now waits forever instead of raising** (executed: `p6_sentinel_nodes.py`)
- **Location:** `_strict.py:250-253` and `:269-270`, where `except OSError: return None` turns every sentinel open error into contention.
- **Trigger:** a directory sits at `resource.lock`.
- **Base:** `IsADirectoryError` immediately.
- **Head:** `Timeout` with `timeout=0.3`, so it would block indefinitely with the default `timeout=-1`. EIO and similar errors are swallowed the same way.
- **Contract:** base surfaced this condition.
- **Same probe, minor variant:** a directory or symlink at the sentinel's private-record name raises a plain `OSError("... is not a regular private record")` (`:554-556`, not wrapped). The same node in the claims directory gives `SoftFileLockProtocolError` (as a test asserts), and how-to says "symlinks ... raise SoftFileLockProtocolError".

**7. A directory-close error after removing the intent claim is silently dropped** (*inferred*)
- **Location:** `_strict.py:165`, where `_unlink_owner_path(intent_path)` is called and its returned error is ignored. The comment at `:702` says "caller commits the removed path before raising", and every other caller raises it.
- **Probe to run:** patch `filelock._strict.os.close` to really close the fd, then raise `OSError(EIO)` on the third directory-fd close of an uncontended acquire. Head acquires and raises nothing. By contrast, `force_break` and `_release` raise the same error.

## Dropped leads
- **Held or intent claims left orphaned when a directory or private-record close fails after a link (`:133-134`, `:154-156`):** this is deliberate. `test_strict_soft_held_directory_close_failure_leaves_both_claims` and `test_strict_soft_private_close_failure_leaves_public_claim` assert it, though it contradicts the comments at `:422` and `:654`.
- **Write failure (ENOSPC) during claim or sentinel publication:** `_publish_record_in_directory` closes the private fd and removes the private record by identity, and the caller sees the original `OSError`.
- **Descriptor leaks on open, fstat or read failure:** `_open_record`, `_publish_record`, `_link_no_replace`, `_unlink_in_directory` and the fstat in `_acquire` all close on every error path.
- **Release failures:** a failed claim unlink keeps the lock held and is retryable (tested). A missing claim or directory counts as already removed.
- **`close_error_policy="suppress"` does not suppress directory-fd close errors on release:** the docs say the policy does not cover marker deletion.
- **Unreadable sentinel owned by another user:** both base and head time out, so behavior is unchanged.
- **Sentinel replaced by a symlink:** both base and head time out (p6).
- **Import-time link probe failing (no temp directory, rmtree error):** caught, and it falls back to `follow_symlinks` defaulting to off.
- **KeyboardInterrupt between a successful link and recording the path:** the window is tiny, and the docs already say a crash can leave claims.
- **Claim with mode 000 or owned by another account:** it retries for 0.5 s and then raises `SoftFileLockProtocolError`, as documented.
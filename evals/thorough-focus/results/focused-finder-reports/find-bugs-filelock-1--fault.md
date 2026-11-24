I found 4 candidates I could not contradict, plus one minor. Probes and outputs are in `<scratch>/out-arm/find-bugs-filelock-1/.scratch/strict-owner-claims/search-1/finder-faults/probes/`, with the exact commands in `COMMANDS.txt`. My base and head worktrees are removed and the checkout is unchanged. I did not touch the other agents' worktrees.

## Candidates

**C1. Errors opening the sentinel are treated as "someone holds the lock" (executed)**
- **Location:** `src/filelock/_strict.py` lines 252–253 and 269–270 (`except OSError: return None` in `_open_or_create_sentinel`), and lines 277–278 (any sentinel content that doesn't match counts as a holder).
- **Trigger:** the lock path is a directory, a read-only or mode-000 file left by another process, or opening it fails with EMFILE (too many open files). The EMFILE case needs a path that has been used before.
- **Base:** `IsADirectoryError` or `PermissionError` (via `raise_on_not_writable_file`), or `OSError [Errno 24]`, raised immediately.
- **Head:** `Timeout` after the full timeout. With the default `timeout=-1` it waits forever. It also leaves `work.lock.filelock/claims` behind.
- **Contract:** the base code says it raises so that "a directory at the lock path" does not make "acquire() block forever on an open that cannot succeed".
- **Probes:** `p1_lockpath_nodes.py` → `p1.out`, and `p4_emfile.py` → `p4.out`, both run at base and head.

**C2. A second account can no longer use a shared lock path (executed)**
- **Location:** lines 93–96 (`_ensure_protocol_directory` uses a bare `mkdir()`; the sentinel and claim directories are permanent). Records are written at line 436.
- **Trigger:** a shared sticky directory such as `/tmp`. uid A acquires and releases, then uid B acquires the free lock.
- **Base:** B acquires, with umask 022, umask 077, or `mode=0o666`.
- **Head:**
  - umask 022: B gets `PermissionError` creating its record in A's 0755 `claims` directory.
  - umask 077: B gets `PermissionError` on `.../claims`.
  - `mode=0o666` does not help, because the directories ignore `mode`.
  - Once directory permissions are fixed, a 0600 sentinel would leave B timing out silently (the C1 path).
- **Contract:** the base worked across accounts. The docs say `mode` and umask control lock-file permissions.
- **Probe:** `p2_cross_account.sh` → `p2.out`. It runs under `setpriv` as uids 65534 and 65533, using copies of `src` in a temporary world-readable `/tmp/fl-probe-*`, since deleted.

**C3. Claims that are already published but never recorded block the lock until an operator steps in (executed, head only)**
- **Locations:**
  - Line 133–134: raises `publication_cleanup_error` before line 135 records `owner_claim_paths`.
  - Line 153–156: records the held path, then sets it back to `()` before raising `link_cleanup_error`.
  - Lines 441 and 457–464: after the public link succeeds, a failure from the identity `lstat`, closing the private file, unlinking the private name, or a `KeyboardInterrupt` raises without removing the public name.
- **Trigger and result:**

| Failure injected | Caller sees | Left on disk | Next contender |
|---|---|---|---|
| Directory fd close fails, intent publication | `OSError` EIO, `is_locked=False` | `intent-…` | `Timeout` |
| Directory fd close fails, held link | `OSError` EIO, `is_locked=False` | `intent-…` and `held-…` | `Timeout` |
| `lstat` EIO after the link | `OSError` EIO | `intent-…` | `Timeout` |
| `KeyboardInterrupt` after the link | `KeyboardInterrupt` | `intent-…` | `Timeout` |
| Private fd close EIO | `OSError` EIO | `intent-…` | `Timeout` |
| Private-name unlink EIO | `OSError` EIO | `intent-…` and the private file | `Timeout` |

- **Base:** `_publish_held_marker` unlinks its marker on any `BaseException` once it has the marker's identity.
- **Contract:** the comments at lines 422 and 654 say "caller records the published/held path before raising". The `release` comments say a failure after the OS unlock keeps state consistent.
- **Probe:** `p3_publish_faults.py` → `p3.out`.

**C4. A filesystem without hard links raises `PermissionError`, not the documented error (executed with an injected fault)**
- **Location:** lines 799–807 (`_raise_if_hard_links_unsupported` recognises only ENOSYS, ENOTSUP, EXDEV and NotImplementedError). It is reached first from the sentinel publish at line 261.
- **Trigger:** `link()` returns EPERM. Linux link(2) uses EPERM for filesystems without hard links, such as vfat and exFAT.
- **Head:** `PermissionError [Errno 1]`. With ENOTSUP the caller does get `SoftFileLockProtocolError`.
- **Contract:** `docs/how-to.rst` says "If hard-link publication is unavailable, acquisition raises `SoftFileLockProtocolError`".
- **Base:** works on these filesystems, since it never creates hard links.
- **Limit:** I could not mount a real vfat volume here (no `mkfs.vfat`), so `os.link` was patched to raise EPERM.
- **Probe:** `p5_link_eperm.py` → `p5.out`.

**C5 (minor). A close error after entering the lock is silently dropped (executed)**
- **Location:** line 165 discards the return value of `_unlink_owner_path(intent_path)`.
- **Trigger:** closing the directory fd fails after the intent unlink.
- **Head:** acquire succeeds and the error is lost. `_release` and `_discard_doorway` raise the same kind of close error.
- **Probe:** `p3.out`, scenario "dir close #3".

## Dropped leads
- **ENOSPC on the record write or the held link:** no claims or descriptors left over, and the next contender acquires (`p6.out`).
- **Symlink at the lock path:** base also times out (`p1.out`).
- **Regular file at `<lock>.filelock`:** head raises the documented `SoftFileLockProtocolError`. Base never used this path.
- **Read-only parent directory:** root bypasses permissions, so not tested. For other users, base and head both raise from `open` or `mkdir`.
- **Explicit `mode` not applied under umask:** base `SoftFileLock` doesn't fchmod either. Same behaviour.
- **`Path.exists()` hiding EACCES in `_read_existing_claims` and `claims`:** Python 3.13 raises `PermissionError` there (checked as uid 65534).
- **Import-time `_probe_link_follow_symlinks` failing with no usable temp directory:** caught as `OSError` and returns False, which is harmless.
- **Release when the claims directory was deleted or replaced by a symlink:** `FileNotFoundError` counts as removed, and ELOOP keeps the lock held and raises. Both fail closed.
- **Non-regular node at a private-record name:** it fails closed as documented. The only flaw is that the wrapped reason reads "cannot list claim directory: OSError" and drops the path, so it's message quality only.
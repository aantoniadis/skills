I read the change once, alone, and ran ten probes. Every value-dependent behaviour I checked was run at both the base and the head, except two inferred results named in candidates 6 and 7.

- **Pins:** base `126cab7` and head `e6538e1`.
- **Probe location:** `<scratch>/out-arm/find-bugs-filelock-0/.scratch/strict-owner-claims/search-1/finder-inputs/probes/`. Each probe has a `.py` script and a `.out` result there, and `COMMANDS.txt` lists the exact commands. Each probe printed `filelock.__file__`, which shows it loaded the `base/` or `head/` worktree in that folder.
- **Checkout:** left unchanged. The two worktrees are still registered in git.

## Candidates

**1. Protocol directories ignore `mode` and inherit the umask, so a second account can't take the lock**
- **Location:** `_strict.py:93-95`. `_ensure_protocol_directory` calls a plain `directory.mkdir()` for `<path>.filelock` and `<path>.filelock/claims`.
- **Trigger:** a shared directory (`1777`). Root, with umask 022, acquires and releases with `mode=0o666`. User `nobody` then acquires the same path.
- **Base:** "second user acquired OK".
- **Head:** both directories are created `0o755`, and the second user gets `PermissionError [Errno 13] ... '.intent-v1-....private-v1-....tmp'`.
- **Contract broken:** `mode` means "file permissions for the lockfile", and a lock shared between accounts worked at the base.
- **Probe:** `p1_multiuser_mode.py` / `.out`.

**2. An unreadable sentinel reads as contention forever, after the holder is gone**
- **Location:** `_strict.py:252-253` and `268-270`. `_open_or_create_sentinel` returns `None` for any `OSError`, and the sentinel is never removed.
- **Trigger:** umask 0 and `mode=0o600`. Root acquires and releases, then `nobody` acquires with `timeout=1`.
- **Base:** acquired.
- **Head:** `Timeout`, with no holder present. With the default `timeout=-1` it would hang forever without an error. `mode=0o644` and unset `mode` work at both.
- **Contract broken:** the lock reports contention when nothing holds it.
- **Probe:** `p3_mode_0600_second_user.py` / `.out`.

**3. Invalid lock paths turn into a silent Timeout instead of an error**
- **Location:** the same lines as candidate 2. The base check `raise_on_not_writable_file` is no longer on this path.
- **Trigger:** the lock path is `""`, `"."` or an existing directory.
- **Base:** `FileNotFoundError` for `""` and `IsADirectoryError` for `"."` and the directory.
- **Head:** `Timeout` for all three. Under the default `timeout=-1` that is an endless wait with no diagnostic.
- **Probe:** `p2_lockpath_values.py` / `.out`. The same output shows a path with a trailing slash (`"new.lock/"`) now acquiring where the base raised; I did not count that as a defect.

**4. A hostname containing whitespace makes the lock unusable on that host**
- **Location:** `_strict.py:395-397`. The writer `_claim_record` records `socket.gethostname()` unchecked, while the reader `_parse_claim` (lines 367-369) rejects whitespace and non-printable characters, including in the process's own claim.
- **Trigger:** hostname `"my host"` or `"host\ttab"`, set with `socket.sethostname` inside `unshare -u`.
- **Base:** acquired twice.
- **Head:** every attempt raises `SoftFileLockProtocolError ... 'intent-v1-....claim': malformed claim record`. Another host scanning while such a claim exists would also fail; that part is inferred. `"héte"` works at both.
- **Probe:** `p6_run.sh` and `p6_hostname_values.py` / `.out`.

**5. A filesystem without hard links raises `PermissionError`, not `SoftFileLockProtocolError`**
- **Location:** `_strict.py:799-807`. `_raise_if_hard_links_unsupported` maps only ENOSYS, ENOTSUP and EXDEV.
- **Why EPERM matters:** Linux `link(2)` returns EPERM when the filesystem "does not support the creation of hard links" (vfat, exfat, some FUSE).
- **Base:** acquired, because it needs no `link`.
- **Head:** `PermissionError: [Errno 1] Operation not permitted`, and `isinstance(e, SoftFileLockProtocolError)` is False.
- **Contract broken:** `docs/how-to.rst` says acquisition raises `SoftFileLockProtocolError` when hard-link publication is unavailable.
- **Probe:** `p7_link_eperm.py` / `.out`. This is instrumented: `os.link` is patched to raise EPERM, because no vfat mount was available here. A real vfat or exfat mount would settle it.

**6. The jittered backoff does nothing at the default `poll_interval` (0.05) or above**
- **Location:** `_api.py` `_poll_delay`. `max(poll_interval, randbelow(window ≤ cap=0.05))` always equals `poll_interval` when `poll_interval >= 0.05`.
- **Base:** fixed sleep.
- **Head:** a single distinct delay at 0.0, 0.05 and 0.1. Jitter only appears below 0.05 (198 distinct delays at 0.001).
- **Contract broken:** commit b072b3b states that contending processes now desynchronize. At the default cadence they stay in the same phase as before.
- **Consequence (inferred):** from reading the code, two contenders can both lose a round (a smaller token publishes after the larger one's second scan), so no-winner rounds can repeat. I did not run a reproduction under contention.
- **Probe:** `p5_backoff_values.py` / `.out`. No test in `tests/` covers `_poll_delay`.

**7. `AsyncStrictSoftFileLock` never backs off**
- **Location:** `asyncio.py` `_async_poll_until_acquired` calls `asyncio.sleep(poll_interval)` and never calls `_poll_delay`.
- **Trigger:** another process holds the lock; acquire with `poll_interval=0.001` and `timeout=0.3`.
- **Head:** the sync lock retried 17 times with 17 distinct delays (max 0.0476). The async lock retried 174 times, every delay exactly 0.001. The base had no backoff in either.
- **Consequence (inferred):** the 8-process lockstep starvation that commit b072b3b fixed for the sync lock remains for async.
- **Probe:** `p8_async_no_backoff.py` / `.out`.

**8. A parent directory that can't be listed now fails the first acquisition**
- **Location:** `_strict.py:536-541`. `_reclaim_sentinel_private_records` calls `os.scandir(path.parent)` whenever the sentinel is missing.
- **Trigger:** the parent directory is mode `0o333` (writable and searchable but not listable), and the user is `nobody`.
- **Base:** acquired.
- **Head:** `PermissionError ... '/tmp/.../dropbox'`.
- **Probe:** `p10_unlistable_parent.py` / `.out`. This setup is niche.

**9. Wrong reason in the `lifetime` warning (message only)**
- **Location:** `_strict.py`. Head no longer sets `_lifetime_unsupported_reason`, so it inherits the base class's text.
- **Base warning:** "a strict lock never reclaims a marker by age".
- **Head warning:** "a native OS lock cannot be broken safely by file age" for a soft lock. The released 3.30.2 in the venv restores a strict-specific reason. The value is dropped at both, so behaviour is the same.
- **Probe:** `p2_lockpath_values.py` / `.out`, last line.

**10. Timeouts overshoot more with a small `poll_interval` (minor)**
- **Cause:** the retry delay can grow to 50 ms, and the code doesn't shorten it to the time left before the timeout.
- **Trigger:** `timeout=0.01`, `poll_interval=0.001`, 20 runs.
- **Base:** median 11.0 ms, max 11.9 ms.
- **Head:** median 15.7 ms, max 23.4 ms. The overshoot can reach about 50 ms with a longer timeout.
- **Probe:** `p9_timeout_overshoot.py` / `.out`.

## Dropped leads
- **`release()` on a shared instance (`thread_local=False`) blocks while another thread waits in `acquire`.** Executed (`p4`): head took 2.74 s and then force-released what the other thread had just acquired; base returned at once. Dropped because the async lock at the base already holds its gate for the whole acquire and releases under it. That is deliberate design, and the sync lock now matches it.
- **API break (`owner`, `pid`, `is_lock_held_by_us`, no-argument `force_break()` removed; marker protocol replaced).** The base's marker-based strict lock is unreleased (`versionadded 3.30.0`), and the released 3.30.2 in the venv already ships the claim protocol.
- **Legacy `SoftFileLock` evicting the sentinel.** `_parse_lock_holder` reads the sentinel as pid 1 on a foreign host, so it counts as held even without the new early return.
- **`poll_interval` of 0, negative, inf or NaN.** These behave as at the base: 0 busy-polls in both, the others raise `ValueError` or the same sleep result. A negative value now raises from `randbelow` instead of `sleep`, still `ValueError`.
- **`thread_local=True` combined with `run_in_executor=True` splitting claim state across threads.** The constructor rejects that combination (`asyncio.py:93`).
- **Fork child unlinking the parent's claims.** `__del__` returns early on a pid mismatch, and the fork reset clears the claim paths.
- **Import-time link probe in `_probe_link_follow_symlinks`.** Every failure is caught; the fallback follows symlinks, but the identity check in `_link_private_record` rejects a swapped source.
- **`preserve_lock_file=True` now accepted.** This is a relaxation, and the sentinel is permanent anyway.
- **Dangling symlink as the lock path.** `Timeout` at both base and head.
- **Livelock between two contenders at the default cadence.** Not reproduced; it stays inferred under candidate 6.
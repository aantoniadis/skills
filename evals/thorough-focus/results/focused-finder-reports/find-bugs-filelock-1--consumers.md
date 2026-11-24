I found seven candidates I could not contradict, and six of them were run at both base and head. This was one read, focused on what code outside the change sees. The probes and their outputs are saved under `<scratch>/out-arm/find-bugs-filelock-1/.scratch/strict-owner-claims/search-1/finder-consumers/probes/`, and `COMMANDS.txt` there has the exact commands. The base and head trees are `git archive` exports in `base/` and `head/` next to it, so the checkout is unchanged. Everything ran on Python 3.13.18, Linux, as root.

## Candidates

**1. Locks with `thread_local=False` can no longer be pickled or deep-copied (every lock class, not only the strict one)**
- **Location:** `src/filelock/_api.py:727`. `__init__` now gives every `BaseFileLock` a `self._transition_lock = RLock()`, although only `StrictSoftFileLock` uses it.
- **Trigger:** `pickle.dumps(lock)` or `copy.deepcopy(lock)` (or deep-copying any object that holds the lock) on a `FileLock`, `SoftFileLock` or `StrictSoftFileLock` built with `thread_local=False`.
- **Base:** pickle and deepcopy return a lock.
- **Head:** `TypeError: cannot pickle '_thread.RLock' object`.
- **Contract:** generic copy and pickle behaviour of unchanged lock classes such as `FileLock`.
- **Limits on impact:**
  - With the default `thread_local=True`, the base already fails (`cannot pickle 'ThreadLocalFileContext'`).
  - At base, a lock pickled into a spawned worker raises "inherited across fork" when used there, so the realistic break is same-process deepcopy (see `p2_spawn.out`).
- **Probe:** `p1_protocols.py`, output in `p1_protocols.out`.

**2. Users other than the first can no longer acquire a strict lock in a shared directory**
- **Location:** `src/filelock/_strict.py:94-95` (`_ensure_protocol_directory`, which calls `directory.mkdir()` and ignores `mode`) and `:123` (`_publish_record` raises any non-EEXIST error).
- **Trigger:** umask 022 and a world-writable sticky directory (like /tmp). User A acquires and releases `StrictSoftFileLock(path, mode=0o666)`. Then user B (another UID) acquires.
- **Base:** "user B acquired".
- **Head:** `<path>.filelock` is created as `0o40755`, owned by A. B gets a raw `PermissionError [Errno 13]` on `.intent-v1-….claim.private-v1-….tmp`. It is not a Timeout or `SoftFileLockProtocolError`, and the error stays permanent because the directory never goes away.
- **Contract:**
  - The `mode` docs in `docs/concepts.rst:488-496` cover only the lock file.
  - Cross-UID sharing worked at base.
  - New docs do not mention the directories' permissions.
- **Probe:** `p3_multiuser.py`, output in `p3_multiuser.out`.

**3. Unchanged how-to section now contradicts head behaviour ("Choose a soft-lock contract")**
- **Location:** `docs/how-to.rst:625-675`. It still says:
  - Strict "never reclaims a marker".
  - Recovery is via `filelock.MarkerSoftFileLock.force_break` (strict no longer subclasses it, and its `force_break` now needs `claim_name`).
  - "Both classes publish a protocol 2 record."
  - The table says `SoftFileLock` with Strict gives "No. The legacy contender evicts the protocol 2 marker."
  - The table says Strict with `SoftFileLease` gives "The lease waits out a strict holder".
- **Trigger:** strict acquires and releases once, then a `SoftFileLease` or `SoftFileLock` contender tries.
- **Base:** both acquire.
- **Head:** both time out permanently, because the sentinel `b'1\nfilelock-strict-v1\x00\n0\n'` stays after release. The lease is therefore locked out for good rather than "waiting out" a holder, and the legacy client no longer evicts anything.
- **Contract:** the new section in `how-to.rst` (about lines 477-560) and `concepts.rst` contradict the old one. The new text names only "legacy clients" as blocked, not `SoftFileLease`.
- **Probe:** `p4_mixed_contracts.py`, output in `p4_mixed_contracts.out`.

**4. `SoftFileLock(path).pid` reports PID 1 on an activated strict path**
- **Location:** `src/filelock/_soft.py` (`pid` property → `_parse_lock_holder`). The sentinel parses as pid=1.
- **Trigger:** a strict lock has run on the path once, then the consumer reads `SoftFileLock(p).pid`.
- **Base:** `None`.
- **Head:** `1`, even with no holder, so a consumer is told init holds the lock.
- **Contract:** the docstring says "The PID of the process holding this lock".
- **Probe:** `p4_mixed_contracts.out`, the "SoftFileLock.pid" line.

**5. The lifetime warning for `StrictSoftFileLock` gives the wrong reason**
- **Location:** `src/filelock/_strict.py:74-83`. The `_lifetime_unsupported_reason` override was dropped, so the class inherits the base class's native-lock text.
- **Trigger:** `StrictSoftFileLock(p, lifetime=5)`.
- **Base:** "…: a strict lock never reclaims a marker by age".
- **Head:** "…: a native OS lock cannot be broken safely by file age".
- **Contract:** the user-facing warning message.
- **Probe:** `p1_protocols.out`, last line of each block.

**6. On a shared strict instance, `release()` blocks while another thread is waiting in `acquire()`**
- **Location:** `src/filelock/_api.py:1121-1122`. `release()` takes `_transition_lock` with a blocking acquire, and a waiting acquirer holds that lock for its whole poll (`_transition_admission`, `:1100-1109`).
- **Trigger:** with `thread_local=False`, thread A calls `acquire(timeout=3)` while another owner holds the path. Thread B calls `shared.release(force=True)`, which is a no-op because nothing is held.
- **Base:** returns in 0.00s.
- **Head:** returns in 2.74s, when A times out. With `timeout=-1` it would block indefinitely.
- **Contract:** a no-op release should not block.
- **Limit:** reach is narrow.
- **Probe:** `p5_release_blocks.py`, output in `p5_release_blocks.out` and `p5_head_full.out`.

**7. The jittered backoff does nothing at the default `poll_interval`**
- **Location:** `src/filelock/_api.py:1238-1247` together with `_poll_backoff_cap = 0.05` (`_strict.py:83`).
- **Cause:** `max(poll_interval, rand ≤ min(cap, …))` always equals `poll_interval` when `poll_interval >= 0.05`, and the default is 0.05.
- **Head:** at 0.05 and 0.1 there is exactly 1 distinct delay value. Only at 0.01 does it vary (758 distinct values).
- **Base:** no backoff exists.
- **Contract:** the code comment says contending processes "desynchronize instead of livelocking".
- **Extra (inferred):** the async poll loop in `asyncio.py` (`_async_poll_until_acquired`) never calls `_poll_delay`, so `AsyncStrictSoftFileLock` gets no backoff at all. Settle it by reading `asyncio.py` around lines 345-375 or by logging the sleep values.
- **Probe:** `p6_poll_delay.py`, head only, output in `p6_poll_delay.out`.

## Dropped leads
- **Strict loses `owner`, `pid`, `is_lock_held_by_us`, the no-argument `force_break()` and its `MarkerSoftFileLock`/`SoftFileLock` subclassing** (confirmed in `p1`): `StrictSoftFileLock` is unreleased (versionadded 3.30.0, latest tag 3.29.7). The changelog fragment 637 and the edited tests show this is intended.
- **Pickling `SoftFileLockProtocolError`:** a round trip keeps the message and `claim_name`, `copy` works, and `errno` is None (`p1`).
- **A legacy `SoftFileLock` or `SoftFileLease` evicting the strict sentinel:** the sentinel parses as a foreign host for `SoftFileLock` and as a non-marker for the lease, so neither breaks it (`p4`). Removal by lifetime is documented.
- **`FileLockContext` gaining `owner_claim_paths` and `claim_root`:** the new fields have defaults and are appended at the end. The class is not exported.
- **The admission gate changing timeout or `blocking=False` semantics for shared instances:** the outcomes match base. At base, concurrent threads raced on one shared context anyway.
- **`__del__` taking `_transition_lock`:** a thread that holds the gate also holds a reference to the lock, so `__del__` cannot run while the gate is held.
- **`ReadWriteLock` and `SoftReadWriteLock` as consumers of `BaseFileLock`:** they are not subclasses.
- **Docs build:** Sphinx is not installed in the venv, so it did not run. The stale `MarkerSoftFileLock.force_break` reference still resolves, so nitpicky mode would not catch it.
- **A symlinked private record in the claims directory raises a plain `OSError`, not `SoftFileLockProtocolError`:** the docs only promise "fails closed" for private-record names. Not probed; treated as minor.
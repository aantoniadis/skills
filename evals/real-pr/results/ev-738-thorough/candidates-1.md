| Candidate | Finders | Disposition |
|---|---|---|
| compacted gen/N+1 re-linked by a participant paused across 65 commits: two holders granted | 2, 3 | delivered |
| same, in leave(): stale commit leaves the released reader named, writers blocked for stale_threshold | 2, 3 | merged into compacted gen/N+1 re-linked by a participant paused across 65 commits: two holders granted |
| fresh-process or short-attempt contenders never evict a dead holder (ledger starts at 0) | 1, 3 | delivered |
| cached _latest outranks a recreated log after <lock>.rw is removed: two writers | 2, 4 | delivered |
| reader release on ENOSPC/EIO raises, hold cleared, reader stays named in snapshot | 5 | delivered |
| planted symlink in holders/ or gen/ makes every acquire raise ELOOP | 5 | delivered |
| planted directory in holders/ makes every acquire raise IsADirectoryError after stale_threshold | 5 | merged into planted symlink in holders/ or gen/ makes every acquire raise ELOOP |
| non-ASCII digit name in gen/ raises ValueError from int() | 1 | delivered |
| ledger grows without bound in a long-lived instance | 1, 2, 3, 4 | delivered |
| latest() probes 64 missing names on every call | 1, 3 | delivered |
| generation docstring fence rejects a live reader | 2 | delivered |
| leave() can busy-loop with no sleep under NFS inconsistency | 5 | dropped: each iteration either commits or loses to a peer that committed (finder 1); an endless loop needs an NFS read/link disagreement no probe showed; kept as unresolved note |

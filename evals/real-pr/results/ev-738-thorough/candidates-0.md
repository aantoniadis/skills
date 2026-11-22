Base 20929f7d1439d5fa1df158fcac87b60815f5d422, head ed3fdd09cf4ebbbc82248fd3df6a5b920734ab8e

| Candidate | Finders | Disposition |
|---|---|---|
| paused commit links a compacted gen/N+1, two writers hold | 1, 2 | delivered |
| same, through leave(): departed holder stays named, writers blocked | 1, 2 | merged into paused commit links a compacted gen/N+1, two writers hold |
| remembered head accepts a stale listing and commits into a dead branch | 4 | merged into paused commit links a compacted gen/N+1, two writers hold |
| fresh short-timeout contenders never evict a dead holder | 3 | delivered |
| ESTALE from os.read after open escapes acquire as bare OSError | 5 | delivered |
| temporary swept during a long pause makes acquire raise FileNotFoundError | 2 | delivered |
| ledger grows by one entry per peer acquisition | 1, 2, 3, 4 | delivered (minor observation, scale-dependent) |
| 64 missing-file opens per latest() call | 3 | delivered (minor observation, scale-dependent) |
| FIFO at own holder record hangs heartbeat and acquire timeout | 5 | delivered (minor observation; same-UID tampering outside docs/concepts.rst:468-476 trust boundary) |
| unreadable stray in holders/ or gen/ makes every acquire raise PermissionError | 5 | delivered (minor observation; needs same-UID chmod 000, outside trust boundary) |
| symlink or mode-000 file at gen/N raises raw OSError, not SoftFileLockProtocolError | 5 | merged into unreadable stray in holders/ or gen/ makes every acquire raise PermissionError |
| mypy head-only diagnostics in tests | 3, 4 | dropped: mypy is not the project checker; ty (pyproject [tool.ty]) shows no head-only diagnostic, tools/ty-delta.txt |

"""Two StrictSoftFileLock contenders both acquire when a scan reads a claim that vanished as its owner won.

Instrumentation only reorders thread scheduling (pauses at points a preempted thread could stop); it does not
alter any file or protocol step. Thread B gets the smaller token so it wins the tie-break; thread A's final scan
lists B's intent claim, is paused before reading it, and resumes after B has linked its held claim and removed
its intent. The read hits ENOENT, the claim is skipped, and A's tie-break sees only its own token.
"""

from __future__ import annotations

import sys
import tempfile
import threading
import types
from pathlib import Path

import filelock
from filelock import StrictSoftFileLock
from filelock import _strict

print("filelock from", filelock.__file__)

TOKENS = {"A": "f" * 32, "B": "0" * 32}
real_secrets = _strict.secrets
local = threading.local()


def token_hex(n: int) -> str:
    who = getattr(local, "who", None)
    # the doorway token is the first token drawn after the first claim scan (the sentinel private name comes earlier)
    if who and getattr(local, "scans", 0) == 1 and not getattr(local, "token_used", False) and n == 16:
        local.token_used = True
        return TOKENS[who]
    return real_secrets.token_hex(n)


_strict.secrets = types.SimpleNamespace(token_hex=token_hex)

ev = {k: threading.Event() for k in ("b_scan1", "a_scan2", "b_scan2", "a_listed", "b_acquired")}
real_scan = _strict._read_existing_claims
real_read = _strict._read_claim_record


def scan(lock_file, directory):
    who = local.who
    local.scans = getattr(local, "scans", 0) + 1
    n = local.scans
    if who == "A" and n == 3:
        local.final_scan = True
    result = real_scan(lock_file, directory)
    local.final_scan = False
    if who == "B" and n == 1:
        ev["b_scan1"].set()
        ev["a_scan2"].wait(5)
    elif who == "B" and n == 2:
        ev["b_scan2"].set()
        ev["a_listed"].wait(5)  # B is preempted before linking its held claim until A's final scan has listed names
    elif who == "A" and n == 2:
        ev["a_scan2"].set()
        ev["b_scan2"].wait(5)
    print(f"{who} scan#{n}: {[c.name[:14] for c in result]}")
    return result


def read(lock_file, directory, name):
    if local.who == "A" and getattr(local, "final_scan", False):
        ev["a_listed"].set()
    if local.who == "A" and getattr(local, "final_scan", False) and name.startswith("intent-") and TOKENS["B"] in name:
        print("A: final scan listed B's intent; pausing before reading it")
        ev["b_acquired"].wait(5)
    return real_read(lock_file, directory, name)


_strict._read_existing_claims = scan
_strict._read_claim_record = read

tmp = Path(tempfile.mkdtemp())
path = str(tmp / "res.lock")
results = {}


def run(who):
    local.who = who
    lock = StrictSoftFileLock(path, blocking=False)
    try:
        lock.acquire()
    except filelock.Timeout:
        results[who] = (lock, False)
    else:
        results[who] = (lock, lock.is_locked)
    if who == "B":
        ev["b_acquired"].set()


tb = threading.Thread(target=run, args=("B",))
tb.start()
ev["b_scan1"].wait(5)
ta = threading.Thread(target=run, args=("A",))
ta.start()
ta.join()
tb.join()
print("A holds:", results["A"][1], "B holds:", results["B"][1])
print("claims on disk:", sorted(p.name[:14] for p in (tmp / "res.lock.filelock" / "claims").iterdir()))
sys.exit(1 if results["A"][1] and results["B"][1] else 0)

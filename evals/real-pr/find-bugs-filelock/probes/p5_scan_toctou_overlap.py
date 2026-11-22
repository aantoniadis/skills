# Two strict contenders both enter: B lists the claim directory and sees intent-A but not held-A; A then links held-A,
# wins its final scan and unlinks intent-A; B's per-record read of intent-A hits ENOENT, is skipped, and B's final
# check no longer sees any claim with A's smaller token.
import os, sys, tempfile, threading
from pathlib import Path
import filelock
from filelock import StrictSoftFileLock

d = tempfile.mkdtemp(); lock_path = Path(d, "resource.lock")
if not hasattr(filelock, "StrictSoftFileClaim"):
    print("base: claim protocol absent (marker lock); scenario not applicable"); raise SystemExit
import filelock._strict as strict
with StrictSoftFileLock(lock_path):
    pass

TOKENS = {"A": "1" * 32, "B": "e" * 32}   # A < B
real_token_hex = strict.secrets.token_hex
def token_hex(n=None):
    name = threading.current_thread().name
    if n == 16 and name in TOKENS:
        return TOKENS[name]
    return real_token_hex(n)
strict.secrets.token_hex = token_hex

ev = {k: (threading.Event(), threading.Event()) for k in ("A1", "B2", "A2", "B3")}  # (reached, go)
def pause(key):
    reached, go = ev[key]; reached.set(); assert go.wait(10), key

scans = {"A": 0, "B": 0}; listings = {"A": 0, "B": 0}
real_read = strict._read_existing_claims
def read_hook(lock_file, directory):
    name = threading.current_thread().name
    result = real_read(lock_file, directory)
    if name in scans:
        scans[name] += 1
        if (name, scans[name]) in {("A", 1), ("B", 2), ("A", 2)}:
            pause(f"{name}{scans[name]}")
    return result
real_list = strict._public_claim_names
def list_hook(directory, entries):
    name = threading.current_thread().name
    names = real_list(directory, entries)
    if name in listings:
        listings[name] += 1
        if (name, listings[name]) == ("B", 3):
            pause("B3")
    return names
strict._read_existing_claims = read_hook
strict._public_claim_names = list_hook

results = {}
def run(name):
    lock = StrictSoftFileLock(lock_path, timeout=5, poll_interval=0.01)
    results[name] = lock
    try:
        lock.acquire()
        results[name] = lock.is_locked  # thread-local context: read in the acquiring thread
    except BaseException as e:
        print(name, "raised", type(e).__name__, e)

def step(key):
    assert ev[key][0].wait(10), f"never reached {key}"
ta = threading.Thread(target=run, args=("A",), name="A"); tb = threading.Thread(target=run, args=("B",), name="B")
ta.start(); step("A1")                       # A passed its empty pre-check
tb.start(); step("B2")                       # B published intent-B and passed S1
ev["A1"][1].set(); step("A2")                # A published intent-A and passed S1 (no held yet)
ev["B2"][1].set(); step("B3")                # B linked held-B and listed {held-B, intent-A, intent-B}
ev["A2"][1].set(); ta.join(10)               # A links held-A, final scan, unlinks intent-A -> owns
ev["B3"][1].set(); tb.join(10)               # B reads records, intent-A gone -> owns
print("alive", ta.is_alive(), tb.is_alive(), "scans", scans, "listings", listings)
print("A is_locked:", results.get("A"), "| B is_locked:", results.get("B"))
print("claims on disk:", sorted(p.name[:14] for p in Path(f"{lock_path}.filelock", "claims").iterdir()))

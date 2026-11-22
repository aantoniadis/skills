"""Probe: a doorway loser whose intent unlink fails is left is_locked=True, and a later acquire 'succeeds'
while another owner's held claim is published.

Fault: the loser's unlink of its own intent claim raises PermissionError once (stands in for a transient
Windows sharing violation / EACCES). A peer's held claim appears between the loser's first scan and its
post-intent scan (stands in for a concurrent winner)."""
import os, sys, tempfile, threading
from pathlib import Path
from unittest import mock
import filelock
from filelock import StrictSoftFileLock, _strict

print("filelock from", filelock.__file__)
d = tempfile.mkdtemp()
path = os.path.join(d, "work.lock")
claims_dir = Path(path + ".filelock", "claims")
peer_token = "f" * 32
peer_held = claims_dir / f"held-v1-{peer_token}.claim"

real_publish = _strict._publish_record
def publish_then_peer_wins(public_path, record, mode):
    result = real_publish(public_path, record, mode)
    if os.path.basename(public_path).startswith("intent-") and not peer_held.exists():
        peer_held.write_bytes(_strict._claim_record(peer_token))  # peer process wins concurrently
    return result

real_unlink = _strict._unlink_in_directory
failures = {"left": 1}
def flaky_unlink(directory, name):
    if name.startswith("intent-") and failures["left"]:
        failures["left"] -= 1
        raise PermissionError(13, "simulated transient sharing violation", name)
    return real_unlink(directory, name)

lock = StrictSoftFileLock(path, thread_local=False, timeout=0.2)
with mock.patch.object(_strict, "_publish_record", publish_then_peer_wins), \
     mock.patch.object(_strict, "_unlink_in_directory", flaky_unlink):
    try:
        lock.acquire()
        print("first acquire: returned (unexpected)")
    except BaseException as e:
        print("first acquire raised:", type(e).__name__, e)

print("after failed acquire: is_locked =", lock.is_locked, "lock_counter =", lock.lock_counter)
print("claims on disk:", sorted(p.name for p in claims_dir.iterdir()))

got = {}
def other_thread():
    try:
        with lock:
            got["entered"] = True
    except BaseException as e:
        got["error"] = repr(e)
t = threading.Thread(target=other_thread); t.start(); t.join()
print("second thread on the shared instance:", got)
print("peer's held claim still published:", peer_held.exists())

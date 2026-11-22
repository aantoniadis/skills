"""Probe: a close() error after the intent claim is published leaves that claim on disk, untracked by the
publisher, so every later contender (and this process) blocks until an operator force-breaks it.
Fault mirrors tests/test_strict_soft_failures.py::test_strict_soft_private_close_failure_leaves_public_claim."""
import os, tempfile
from errno import EIO
from unittest import mock
import filelock
from filelock import StrictSoftFileLock, Timeout, _strict

print("filelock from", filelock.__file__)
path = os.path.join(tempfile.mkdtemp(), "work.lock")
# initialize protocol with a clean acquire/release
l0 = StrictSoftFileLock(path); l0.acquire(); l0.release()

real_close = os.close
state = {"armed": True}
def fail_first_close(fd):
    real_close(fd)
    if state["armed"]:
        state["armed"] = False
        raise OSError(EIO, "private close failed")

lock = StrictSoftFileLock(path)
with mock.patch.object(_strict.os, "close", side_effect=fail_first_close):
    try:
        lock.acquire()
    except OSError as e:
        print("acquire raised:", e)
print("is_locked:", lock.is_locked, "owner_claim_paths:", lock._context.owner_claim_paths)
print("claims:", [(c.state, c.pid == os.getpid()) for c in lock.claims])
for who, contender in (("same instance", lock), ("fresh instance", StrictSoftFileLock(path))):
    try:
        contender.acquire(timeout=1); print(who, "acquired"); contender.release()
    except Timeout:
        print(who, "-> Timeout (blocked by own orphaned claim)")

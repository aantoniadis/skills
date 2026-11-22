import os, pickle, socket, stat, sys, tempfile, threading, time, warnings
from unittest import mock
import filelock
from filelock import FileLock, StrictSoftFileLock, Timeout
tmp = tempfile.mkdtemp(); p = lambda n: os.path.join(tmp, n)
def show(tag, fn):
    try: print(tag, fn())
    except BaseException as e: print(tag, "RAISES", type(e).__name__, str(e)[:110])
# F3 lifetime warning text
def f3():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always"); StrictSoftFileLock(p("f3.lock"), lifetime=5)
    return [str(x.message)[-70:] for x in w]
show("F3 lifetime warning:", f3)
# F13 pickle of a non-thread-local native lock
show("F13 pickle FileLock(thread_local=False):", lambda: len(pickle.dumps(FileLock(p("f13.lock"), thread_local=False))) > 0)
# F12 hostname with whitespace
def f12():
    with mock.patch.object(socket, "gethostname", return_value="my host"):
        l = StrictSoftFileLock(p("f12.lock"), timeout=1); l.acquire(); l.release(); return "acquired"
show("F12 whitespace hostname:", f12)
# F6 lock path is a directory
def f6():
    d = p("f6dir"); os.mkdir(d); t = time.time()
    try: StrictSoftFileLock(d, timeout=0.5).acquire(); return "acquired"
    finally: print("   F6 elapsed %.2fs" % (time.time() - t))
show("F6 path is a directory:", f6)
# F1 modes of the coordination directories
def f1():
    os.umask(0o022); path = p("f1.lock"); l = StrictSoftFileLock(path, mode=0o666); l.acquire(); l.release()
    out = {}
    for name in (path, path + ".filelock", os.path.join(path + ".filelock", "claims")):
        if os.path.exists(name): out[os.path.basename(name)] = oct(stat.S_IMODE(os.stat(name).st_mode))
    return out
show("F1 modes with mode=0o666, umask 022:", f1)
# F5 release() on an unheld shared instance while another thread waits in acquire()
def f5():
    path = p("f5.lock"); owner = StrictSoftFileLock(path); owner.acquire()
    shared = StrictSoftFileLock(path, thread_local=False, timeout=2.0)
    def waiter():
        try: shared.acquire()
        except Timeout: pass
    t = threading.Thread(target=waiter); t.start(); time.sleep(0.4)
    t0 = time.time(); shared.release(); blocked = time.time() - t0
    t.join(); owner.release(); return "release() blocked %.2fs" % blocked
show("F5 release on unheld shared instance:", f5)
# F11 non-blocking re-entry into a held shared instance from several threads
def f11():
    shared = StrictSoftFileLock(p("f11.lock"), thread_local=False); shared.acquire(); errs = []
    def hammer():
        for _ in range(300):
            try: shared.acquire(blocking=False); shared.release()
            except Timeout: errs.append(1)
    ts = [threading.Thread(target=hammer) for _ in range(8)]; [t.start() for t in ts]; [t.join() for t in ts]
    shared.release(); return "%d Timeout in 2400 re-entries" % len(errs)
show("F11 non-blocking re-entry:", f11)

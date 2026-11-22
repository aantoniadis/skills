import sys, threading, warnings
warnings.simplefilter("ignore")
from fastapi import APIRouter, FastAPI
import fastapi.routing as R
from fastapi.testclient import TestClient
N_ROUTES, N_THREADS = 120, 6
app = FastAPI(); router = APIRouter()
for i in range(N_ROUTES):
    def endpoint(i: int = i): return {"i": i}
    router.add_api_route(f"/r{i}", endpoint, methods=["GET"])
app.include_router(router)
sys.setswitchinterval(1e-5)
barrier = threading.Barrier(N_THREADS); codes = []
def worker():
    c = TestClient(app); barrier.wait(); codes.append(c.get(f"/r{N_ROUTES - 1}").status_code)
ts = [threading.Thread(target=worker) for _ in range(N_THREADS)]
[t.start() for t in ts]; [t.join() for t in ts]
inc = [r for r in app.router.routes if type(r).__name__ == "_IncludedRouter"]
print("K3 status codes:", sorted(codes), "| cached candidates:", len(inc[0]._effective_candidates) if inc else "n/a (no _IncludedRouter)", "expected", N_ROUTES)

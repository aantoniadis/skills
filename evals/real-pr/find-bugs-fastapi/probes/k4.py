from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from starlette.testclient import TestClient
app = FastAPI(); child = APIRouter()
@child.get("/child")
def read_child(): return {"m": 1}
app.include_router(child, prefix="/api")
c = TestClient(app); c.get("/api/child")
def two(): return {"m": 2}
child.routes.append(APIRoute("/child2", two, methods=["GET"]))
print("K4 direct-append status", c.get("/api/child2").status_code)

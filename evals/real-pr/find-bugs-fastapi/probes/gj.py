import warnings; warnings.simplefilter("ignore")
from pydantic import BaseModel
from fastapi import APIRouter, FastAPI
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient
def subapp(): return Starlette(routes=[Route("/", lambda r: PlainTextResponse("ok"))])
sub = APIRouter()
@sub.get("/a")
def a(): return 1
app = FastAPI(); app.include_router(sub, prefix="/p"); sub.mount("/m", subapp())
c = TestClient(app); print("G mount before first request:", c.get("/p/m/").status_code)
class M(BaseModel): x: int = 0
r = APIRouter()
@r.get("/ok")
def ok(): return {"x": 1}
app = FastAPI()
@app.get("/root")
def root(): return 1
try:
    app.include_router(r, prefix="/r", responses={204: {"model": M}})
    c = TestClient(app, raise_server_exceptions=False)
    print("J include accepted; GET /r/ok ->", c.get("/r/ok").status_code, "| GET /root ->", c.get("/root").status_code)
except AssertionError as e: print("J include raises AssertionError:", str(e)[:70])

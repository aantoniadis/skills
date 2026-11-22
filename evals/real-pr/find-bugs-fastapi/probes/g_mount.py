import warnings; warnings.simplefilter("ignore")
from fastapi import APIRouter, FastAPI
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient
sub = APIRouter()
@sub.get("/a")
def a(): return 1
app = FastAPI(); app.include_router(sub, prefix="/p"); c = TestClient(app); c.get("/p/a")
sub.mount("/m", Starlette(routes=[Route("/", lambda r: PlainTextResponse("ok"))]))
print("G mount-after-include status:", c.get("/p/m/").status_code)

import warnings; warnings.simplefilter("ignore")
from fastapi import APIRouter, FastAPI
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient
async def plain(request): return PlainTextResponse("ok")
child = APIRouter(); child.add_route("/plain", plain)
parent = APIRouter(prefix="/api"); parent.include_router(child)
app = FastAPI(); app.include_router(parent); c = TestClient(app)
print("N8 /plain:", c.get("/plain").status_code, "| /api/plain:", c.get("/api/plain").status_code)
class SlashRouter(APIRouter):
    def add_api_route(self, path, endpoint, **kw):
        super().add_api_route(path, endpoint, **kw)
        if not path.endswith("/"): super().add_api_route(path + "/", endpoint, **kw)
child = APIRouter()
@child.get("/x")
def x(): return 1
parent = SlashRouter(); parent.include_router(child, prefix="/c")
app = FastAPI(); app.include_router(parent); c = TestClient(app, follow_redirects=False)
print("N9 /c/x:", c.get("/c/x").status_code, "| /c/x/:", c.get("/c/x/").status_code)

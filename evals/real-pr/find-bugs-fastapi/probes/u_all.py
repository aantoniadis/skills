import warnings; warnings.simplefilter("ignore")
from fastapi import FastAPI, APIRouter, Request
from fastapi.routing import APIRoute
from fastapi.openapi.utils import get_openapi
from starlette.testclient import TestClient

# B: assigned openapi_schema
app = FastAPI(); app.openapi_schema = {"openapi": "3.1.0", "info": {"title": "custom", "version": "1"}, "paths": {}}
print("B openapi title:", TestClient(app).get("/openapi.json").json()["info"]["title"])

# C: callbacks from a callback router that includes another router
inner = APIRouter()
@inner.post("{$callback_url}/ev")
def ev(): ...
cb = APIRouter(); cb.include_router(inner)
app = FastAPI()
@app.post("/hook", callbacks=cb.routes)
def hook(): ...
print("C callbacks:", list(app.openapi()["paths"]["/hook"]["post"].get("callbacks", {}).keys()))

# F: object passed to generate_unique_id_function for an included route
seen = []
def uid(route): seen.append(type(route).__name__); return route.name
r = APIRouter()
@r.get("/x")
def x(): ...
app = FastAPI(generate_unique_id_function=uid); app.include_router(r, prefix="/p"); app.openapi()
print("F unique-id arg types:", sorted(set(seen)))

# H: route class that wraps self.app in __init__
class Wrapped(APIRoute):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        orig = self.app
        async def wrapper(scope, receive, send):
            scope["wrapped"] = True
            await orig(scope, receive, send)
        self.app = wrapper
r = APIRouter(route_class=Wrapped)
@r.get("/w")
def w(request: Request): return {"wrapped": request.scope.get("wrapped", False)}
app = FastAPI(); app.include_router(r)
print("H wrapper applied:", TestClient(app).get("/w").json())

# I: get_openapi(routes=None)
try:
    get_openapi(title="t", version="1", routes=None); print("I routes=None ok")
except Exception as e: print("I RAISES", type(e).__name__, str(e)[:60])

# E: get_route_handler calls per request for an included route
calls = []
class Counting(APIRoute):
    def get_route_handler(self):
        calls.append(1); return super().get_route_handler()
r = APIRouter(route_class=Counting)
@r.get("/c")
def c(): return 1
app = FastAPI(); app.include_router(r); cl = TestClient(app); n0 = len(calls)
for _ in range(5): cl.get("/c")
print("E get_route_handler calls during 5 requests:", len(calls) - n0)

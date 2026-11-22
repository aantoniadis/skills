from fastapi import APIRouter, FastAPI, Request
from starlette.testclient import TestClient
app = FastAPI(); r1 = APIRouter(prefix="/level1"); r2 = APIRouter(prefix="/level2")
@r2.get("/endpoint")
def handle(request: Request): return {"route.path": request.scope["route"].path}
r1.include_router(r2); app.include_router(r1)
print("K5", TestClient(app).get("/level1/level2/endpoint").json())

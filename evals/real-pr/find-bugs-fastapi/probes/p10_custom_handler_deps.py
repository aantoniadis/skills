# Custom APIRoute that builds its handler from its own attributes (no super().get_route_handler()).
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.routing import APIRoute, get_request_handler
from fastapi.testclient import TestClient
class MyRoute(APIRoute):
    def get_route_handler(self):
        return get_request_handler(dependant=self.dependant, body_field=self.body_field,
            status_code=self.status_code, response_class=self.response_class,
            response_field=self.response_field, embed_body_fields=self._embed_body_fields,
            dependency_overrides_provider=self.dependency_overrides_provider)
def auth(): raise HTTPException(401)
router = APIRouter(route_class=MyRoute)
@router.get("/secret")
def secret(): return "data"
app = FastAPI()
app.include_router(router, prefix="/r", dependencies=[Depends(auth)])
print("GET /r/secret ->", TestClient(app).get("/r/secret").status_code)

from fastapi import FastAPI, APIRouter
leaf = APIRouter()
@leaf.get("")
def list_items(): return []
inner = APIRouter(); inner.include_router(leaf, prefix="/items")
app = FastAPI()
try:
    app.include_router(inner); print("K1 ok routes registered")
except Exception as e: print("K1 RAISES", type(e).__name__, e)

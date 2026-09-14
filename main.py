import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.searching_recipe_ai import router as recipe_ai_router
from database.db import init_db_pool, close_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()

app = FastAPI(
    title="ResepKita AI",
    version="1.0.0",
    lifespan=lifespan
)

public_dir = os.path.join(os.path.dirname(__file__), "Public")
if os.path.exists(public_dir):
    app.mount("/static", StaticFiles(directory=public_dir), name="static")

app.include_router(recipe_ai_router)

@app.get("/")
async def root():
    return {"status": "ok"}

application = app

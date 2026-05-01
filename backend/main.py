from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.pool import init_db_pool, close_db_pool
from config import settings
from api.routes import documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool(settings.database_url)
    yield
    await close_db_pool()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(documents.router)
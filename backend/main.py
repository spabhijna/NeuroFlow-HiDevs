import asyncio
from contextlib import asynccontextmanager

from arq.connections import RedisSettings, create_pool
from fastapi import FastAPI

try:
    from backend.api import ingest
    from backend.api.routes import documents
    from backend.config import settings
    from backend.db.pool import init_db_pool, close_db_pool
except ModuleNotFoundError:
    from api import ingest
    from api.routes import documents
    from config import settings
    from db.pool import init_db_pool, close_db_pool


async def _close_redis_pool(redis) -> None:
    close_result = redis.close()
    if asyncio.iscoroutine(close_result):
        await close_result

    wait_closed = getattr(redis, "wait_closed", None)
    if callable(wait_closed):
        await wait_closed()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool(settings.database_url)
    app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        yield
    finally:
        await _close_redis_pool(app.state.redis)
        await close_db_pool()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(documents.router)
app.include_router(ingest.router)
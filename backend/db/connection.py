from contextlib import asynccontextmanager

try:
    from backend.db import pool as db_pool
except ModuleNotFoundError:
    from db import pool as db_pool
@asynccontextmanager
async def get_connection(pipeline_id: str):
    async with db_pool.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "SELECT set_config('app.current_pipeline_id', $1, true)",
                pipeline_id,
            )
            yield conn
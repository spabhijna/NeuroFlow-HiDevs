import asyncpg
from typing import Optional

pool: Optional[asyncpg.Pool] = None

async def init_db_pool(database_url: str):
    global pool
    pool = await asyncpg.create_pool(
        database_url,
        min_size=5,
        max_size=20,
    )

async def close_db_pool():
    global pool
    if pool:
        await pool.close()
from fastapi import Depends, Header

try:
    from backend.db.connection import get_connection
except ModuleNotFoundError:
    from db.connection import get_connection

async def get_pipeline_id(x_pipeline_id: str = Header(...)):
    return x_pipeline_id

async def get_db_conn(pipeline_id: str = Depends(get_pipeline_id)):
    async with get_connection(pipeline_id) as conn:
        yield conn
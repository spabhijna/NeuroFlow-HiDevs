from fastapi import APIRouter, Depends

try:
    from backend.api.dependencies import get_db_conn
except ModuleNotFoundError:
    from api.dependencies import get_db_conn

router = APIRouter()

@router.get("/documents")
async def get_documents(conn = Depends(get_db_conn)):
    rows = await conn.fetch("SELECT * FROM documents")
    return [dict(r) for r in rows]
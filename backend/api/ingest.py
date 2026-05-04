import hashlib
import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

try:
	from backend.api.dependencies import get_db_conn, get_pipeline_id
except ModuleNotFoundError:
	from api.dependencies import get_db_conn, get_pipeline_id

router = APIRouter()

STORAGE_DIR = os.getenv("INGEST_STORAGE_DIR", "data/ingestion")

SOURCE_TYPE_MAP = {
	".pdf": "pdf",
	".docx": "docx",
	".csv": "csv",
	".png": "image",
	".jpg": "image",
	".jpeg": "image",
	".gif": "image",
	".webp": "image",
	".txt": "text",
}


def _detect_source_type(filename: str) -> str:
	_, ext = os.path.splitext(filename)
	source_type = SOURCE_TYPE_MAP.get(ext.lower())
	if source_type is None:
		raise HTTPException(status_code=400, detail="Unsupported file type")
	return source_type


async def _write_file_and_hash(file: UploadFile, destination: str) -> str:
	hasher = hashlib.sha256()
	os.makedirs(os.path.dirname(destination), exist_ok=True)

	with open(destination, "wb") as out:
		while True:
			chunk = await file.read(1024 * 1024)
			if not chunk:
				break
			hasher.update(chunk)
			out.write(chunk)

	return hasher.hexdigest()


@router.post("/ingest")
async def ingest(
	request: Request,
	file: UploadFile = File(...),
	conn=Depends(get_db_conn),
	pipeline_id: str = Depends(get_pipeline_id),
):
	if not file.filename:
		raise HTTPException(status_code=400, detail="Filename is required")

	source_type = _detect_source_type(file.filename)
	document_id = uuid.uuid4()
	_, ext = os.path.splitext(file.filename)
	file_path = os.path.join(STORAGE_DIR, f"{document_id}{ext.lower()}")
	content_hash = await _write_file_and_hash(file, file_path)

	existing = await conn.fetchrow(
		"SELECT id, status FROM documents WHERE content_hash = $1",
		content_hash,
	)
	if existing:
		if os.path.exists(file_path):
			os.remove(file_path)
		return {
			"document_id": str(existing["id"]),
			"status": existing["status"],
			"duplicate": True,
		}

	await conn.execute(
		"""
		INSERT INTO documents
			(id, filename, source_type, content_hash, metadata, pipeline_id, status)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		""",
		document_id,
		file.filename,
		source_type,
		content_hash,
		json.dumps({}),
		pipeline_id,
		"queued",
	)

	redis = request.app.state.redis
	await redis.enqueue_job(
		"process_document",
		str(document_id),
		file_path,
		source_type,
		pipeline_id,
	)

	return {
		"document_id": str(document_id),
		"status": "queued",
		"duplicate": False,
	}

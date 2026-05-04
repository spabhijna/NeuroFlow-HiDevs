import hashlib
import json
import os
import uuid
from urllib.parse import urlparse

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

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


def _validate_url(raw_url: str) -> str:
	parsed = urlparse(raw_url.strip())
	if parsed.scheme not in {"http", "https"} or not parsed.netloc:
		raise HTTPException(status_code=400, detail="Invalid URL")
	return raw_url.strip()


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
	conn=Depends(get_db_conn),
	pipeline_id: str = Depends(get_pipeline_id),
):
	source_type: str
	filename: str
	file_path: str
	content_hash: str
	metadata: dict[str, str] = {}

	document_id = uuid.uuid4()
	content_type = request.headers.get("content-type", "")

	if "multipart/form-data" in content_type:
		form = await request.form()
		file = form.get("file")
		if file is not None and (not hasattr(file, "filename") or not hasattr(file, "read")):
			raise HTTPException(status_code=400, detail="Invalid file field")
	else:
		file = None

	if file is not None:
		if not file.filename:
			raise HTTPException(status_code=400, detail="Filename is required")
		source_type = _detect_source_type(file.filename)
		filename = file.filename
		_, ext = os.path.splitext(file.filename)
		file_path = os.path.join(STORAGE_DIR, f"{document_id}{ext.lower()}")
		content_hash = await _write_file_and_hash(file, file_path)
	elif "application/json" in content_type:
		payload = await request.json()
		raw_url = payload.get("url") if isinstance(payload, dict) else None
		if not raw_url:
			raise HTTPException(status_code=400, detail="url is required")
		normalized_url = _validate_url(raw_url)
		source_type = "url"
		filename = normalized_url
		file_path = normalized_url
		content_hash = hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()
		metadata = {"url": normalized_url}
	else:
		raise HTTPException(
			status_code=400,
			detail="Provide either multipart file upload or JSON body with url",
		)

	existing = await conn.fetchrow(
		"""
		SELECT id, status
		FROM documents
		WHERE content_hash = $1 AND pipeline_id = $2
		""",
		content_hash,
		pipeline_id,
	)
	if existing:
		if file is not None and os.path.exists(file_path):
			os.remove(file_path)
		return {
			"document_id": str(existing["id"]),
			"status": existing["status"],
			"duplicate": True,
		}

	try:
		await conn.execute(
			"""
			INSERT INTO documents
				(id, filename, source_type, content_hash, metadata, pipeline_id, status)
			VALUES ($1, $2, $3, $4, $5, $6, $7)
			""",
			document_id,
			filename,
			source_type,
			content_hash,
			json.dumps(metadata),
			pipeline_id,
			"queued",
		)
	except asyncpg.UniqueViolationError:
		# Handle concurrent uploads of the same source deterministically.
		existing = await conn.fetchrow(
			"""
			SELECT id, status
			FROM documents
			WHERE content_hash = $1 AND pipeline_id = $2
			""",
			content_hash,
			pipeline_id,
		)
		if existing:
			if file is not None and os.path.exists(file_path):
				os.remove(file_path)
			return {
				"document_id": str(existing["id"]),
				"status": existing["status"],
				"duplicate": True,
			}
		raise

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

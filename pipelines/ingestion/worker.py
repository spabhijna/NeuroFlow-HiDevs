import json

from arq.connections import RedisSettings

try:
	from backend.config import settings
	from backend.db.connection import get_connection
	from backend.db.pool import init_db_pool, close_db_pool
except ModuleNotFoundError:
	from config import settings
	from db.connection import get_connection
	from db.pool import init_db_pool, close_db_pool
from pipelines.ingestion import ExtractedPage
from pipelines.ingestion.chunker import fixed_size_chunk
from pipelines.ingestion.extractors import get_extractor


async def process_document(
	ctx,
	document_id: str,
	file_path: str,
	source_type: str,
	pipeline_id: str,
):
	print(f"Processing {document_id}")

	try:
		status = await _get_document_status(pipeline_id, document_id)
		if status is None:
			print(f"Document not found: {document_id}")
			return
		if status == "complete":
			print(f"Already complete: {document_id}")
			return

		await _set_status(pipeline_id, document_id, "processing")

		extractor = get_extractor(source_type)
		pages = extractor(file_path)
		chunk_rows = _build_chunks(pages)
		await _store_chunks(pipeline_id, document_id, chunk_rows)
		await _set_complete(pipeline_id, document_id, len(chunk_rows))
	except Exception as exc:
		await _set_status(pipeline_id, document_id, "failed")
		print(f"Failed {document_id}: {exc}")
		raise


async def _get_document_status(pipeline_id: str, document_id: str) -> str | None:
	async with get_connection(pipeline_id) as conn:
		row = await conn.fetchrow(
			"SELECT status FROM documents WHERE id = $1",
			document_id,
		)
		return row["status"] if row else None


async def _set_status(pipeline_id: str, document_id: str, status: str) -> None:
	async with get_connection(pipeline_id) as conn:
		await conn.execute(
			"UPDATE documents SET status = $1 WHERE id = $2",
			status,
			document_id,
		)


def _build_chunks(pages: list[ExtractedPage]) -> list[tuple[str, int, int, dict]]:
	rows: list[tuple[str, int, int, dict]] = []
	chunk_index = 0

	for page in pages:
		for chunk in fixed_size_chunk(page.content, size=512):
			metadata = {
				"page_number": page.page_number,
				"content_type": page.content_type,
			}
			if page.metadata:
				metadata.update(page.metadata)

			token_count = len(chunk.split())
			rows.append((chunk, chunk_index, token_count, metadata))
			chunk_index += 1

	return rows


async def _store_chunks(
	pipeline_id: str,
	document_id: str,
	rows: list[tuple[str, int, int, dict]],
) -> None:
	if not rows:
		return

	values = [
		(document_id, row[0], row[1], row[2], json.dumps(row[3]))
		for row in rows
	]

	async with get_connection(pipeline_id) as conn:
		await conn.executemany(
			"""
			INSERT INTO chunks (document_id, content, chunk_index, token_count, metadata)
			VALUES ($1, $2, $3, $4, $5)
			""",
			values,
		)


async def _set_complete(
	pipeline_id: str,
	document_id: str,
	chunk_count: int,
) -> None:
	async with get_connection(pipeline_id) as conn:
		await conn.execute(
			"UPDATE documents SET status = $1, chunk_count = $2 WHERE id = $3",
			"complete",
			chunk_count,
			document_id,
		)


async def startup(ctx) -> None:
	await init_db_pool(settings.database_url)


async def shutdown(ctx) -> None:
	await close_db_pool()


class WorkerSettings:
	functions = [process_document]
	redis_settings = RedisSettings.from_dsn(settings.redis_url)
	on_startup = startup
	on_shutdown = shutdown

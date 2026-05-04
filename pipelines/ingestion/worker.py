import json
import logging
import time
from collections.abc import Awaitable

from arq.connections import RedisSettings
from opentelemetry import trace

try:
	from backend.config import settings
	from backend.db.connection import get_connection
	from backend.db.pool import init_db_pool, close_db_pool
except ModuleNotFoundError:
	from config import settings
	from db.connection import get_connection
	from db.pool import init_db_pool, close_db_pool
from pipelines.ingestion import ExtractedPage
from pipelines.ingestion.chunker import fixed_size_chunk, hierarchical_chunk, semantic_chunk
from pipelines.ingestion.extractors import get_extractor

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
logging.basicConfig(level=logging.INFO)


async def process_document(
	ctx,
	document_id: str,
	file_path: str,
	source_type: str,
	pipeline_id: str,
):
	started_at = time.perf_counter()
	with tracer.start_as_current_span("ingestion.process") as span:
		span.set_attribute("document_id", document_id)
		span.set_attribute("source_type", source_type)
		span.set_attribute("pipeline_id", pipeline_id)

		try:
			status = await _get_document_status(pipeline_id, document_id)
			if status is None:
				logger.warning("document_not_found", extra={"document_id": document_id})
				return
			if status == "complete":
				logger.info("document_already_complete", extra={"document_id": document_id})
				return

			await _set_status(pipeline_id, document_id, "processing")

			extractor = get_extractor(source_type)
			extracted = extractor(file_path)
			pages = await extracted if isinstance(extracted, Awaitable) else extracted
			chunk_rows = _build_chunks(pages, source_type)
			await _store_chunks(pipeline_id, document_id, chunk_rows)
			await _set_complete(pipeline_id, document_id, len(chunk_rows))

			page_count = len(pages)
			chunk_count = len(chunk_rows)
			total_tokens = sum(row[2] for row in chunk_rows)
			duration_ms = int((time.perf_counter() - started_at) * 1000)
			span.set_attribute("page_count", page_count)
			span.set_attribute("chunk_count", chunk_count)
			logger.info(
				json.dumps(
					{
						"event": "ingestion_complete",
						"document_id": document_id,
						"duration_ms": duration_ms,
						"chunks": chunk_count,
						"tokens": total_tokens,
					}
				)
			)
		except Exception as exc:
			await _set_status(pipeline_id, document_id, "failed")
			logger.exception("ingestion_failed", extra={"document_id": document_id})
			raise exc


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


def _select_chunk_strategy(pages: list[ExtractedPage], source_type: str) -> str:
	if any(page.content_type == "table" for page in pages):
		return "fixed_size"
	if source_type == "docx" and any(
		"heading_path" in page.metadata for page in pages if page.metadata
	):
		return "hierarchical"
	if source_type == "pdf" and len(pages) > 50:
		return "semantic"
	return "fixed_size"


def _build_chunks(
	pages: list[ExtractedPage],
	source_type: str,
) -> list[tuple[str, int, int, dict]]:
	rows: list[tuple[str, int, int, dict]] = []
	chunk_index = 0
	strategy = _select_chunk_strategy(pages, source_type)

	if strategy == "hierarchical":
		for chunk, chunk_metadata in hierarchical_chunk(pages, size=512):
			if not chunk.strip():
				continue
			metadata = {
				"chunk_strategy": strategy,
				**chunk_metadata,
			}
			token_count = len(chunk.split())
			rows.append((chunk, chunk_index, token_count, metadata))
			chunk_index += 1
		return rows

	for page in pages:
		if strategy == "semantic":
			page_chunks = semantic_chunk(page.content, threshold=0.7)
		else:
			page_chunks = fixed_size_chunk(page.content, size=512)
		for chunk in page_chunks:
			if not chunk.strip():
				continue
			metadata = {
				"page_number": page.page_number,
				"content_type": page.content_type,
				"chunk_strategy": strategy,
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

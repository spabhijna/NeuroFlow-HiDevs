from pipelines.ingestion import ExtractedPage
from pipelines.ingestion.chunker import hierarchical_chunk, semantic_chunk
from pipelines.ingestion.worker import _select_chunk_strategy


def test_semantic_chunk_splits_text():
	text = "Alpha sentence. Beta sentence. Gamma sentence!"
	chunks = semantic_chunk(text, threshold=0.9999)
	assert len(chunks) >= 2


def test_hierarchical_chunk_adds_parent_and_children():
	pages = [
		ExtractedPage(
			page_number=1,
			content="Overview paragraph for section one.",
			content_type="text",
			metadata={"heading_path": ["Section One"]},
		)
	]
	rows = hierarchical_chunk(pages, size=20)
	assert any(meta["relation"] == "parent" for _, meta in rows)
	assert any(meta["relation"] == "child" for _, meta in rows)


def test_strategy_selection_rules():
	table_pages = [ExtractedPage(1, "a,b", "table", {})]
	assert _select_chunk_strategy(table_pages, "csv") == "fixed_size"

	docx_pages = [ExtractedPage(1, "Heading", "heading", {"heading_path": ["H1"]})]
	assert _select_chunk_strategy(docx_pages, "docx") == "hierarchical"

	pdf_pages = [ExtractedPage(i, f"text {i}", "text", {}) for i in range(1, 55)]
	assert _select_chunk_strategy(pdf_pages, "pdf") == "semantic"

from collections.abc import Awaitable, Callable

from pipelines.ingestion import ExtractedPage
from pipelines.ingestion.extractors.csv_extractor import extract_csv
from pipelines.ingestion.extractors.docx_extractor import extract_docx
from pipelines.ingestion.extractors.image_extractor import extract_image
from pipelines.ingestion.extractors.pdf_extractor import extract_pdf
from pipelines.ingestion.extractors.url_extractor import extract_url

Extractor = Callable[[str], list[ExtractedPage] | Awaitable[list[ExtractedPage]]]

EXTRACTOR_REGISTRY: dict[str, Extractor] = {
	"pdf": extract_pdf,
	"docx": extract_docx,
	"image": extract_image,
	"csv": extract_csv,
	"url": extract_url,
}


def get_extractor(source_type: str) -> Extractor:
	extractor = EXTRACTOR_REGISTRY.get(source_type)
	if extractor is None:
		raise ValueError(f"Unsupported source_type: {source_type}")
	return extractor

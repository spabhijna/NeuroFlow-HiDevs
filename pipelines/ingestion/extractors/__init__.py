from typing import Callable

from pipelines.ingestion import ExtractedPage
from pipelines.ingestion.extractors.pdf_extractor import extract_pdf

Extractor = Callable[[str], list[ExtractedPage]]

EXTRACTOR_REGISTRY: dict[str, Extractor] = {
	"pdf": extract_pdf,
}


def get_extractor(source_type: str) -> Extractor:
	extractor = EXTRACTOR_REGISTRY.get(source_type)
	if extractor is None:
		raise ValueError(f"Unsupported source_type: {source_type}")
	return extractor

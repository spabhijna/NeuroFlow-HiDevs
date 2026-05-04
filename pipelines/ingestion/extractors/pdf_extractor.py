from pipelines.ingestion import ExtractedPage


def extract_pdf(file_path: str) -> list[ExtractedPage]:
	_ = file_path
	return [
		ExtractedPage(
			page_number=1,
			content="dummy text",
			content_type="text",
			metadata={},
		)
	]

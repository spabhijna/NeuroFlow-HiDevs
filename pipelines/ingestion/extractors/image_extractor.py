from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from pipelines.ingestion import ExtractedPage

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _generate_image_description_stub(image: Image.Image) -> str:
	return f"Image description unavailable (stub). Size: {image.width}x{image.height}."


def extract_image(file_path: str) -> list[ExtractedPage]:
	ext = Path(file_path).suffix.lower()
	if ext not in SUPPORTED_IMAGE_EXTENSIONS:
		raise ValueError(f"Unsupported image format: {ext}")

	with Image.open(file_path) as img:
		image = img.convert("RGB")
		image.thumbnail((1024, 1024))
		try:
			ocr_text = pytesseract.image_to_string(image).strip()
		except Exception:
			ocr_text = ""
		description = _generate_image_description_stub(image)

	content = description + "\n\nText found in image: " + ocr_text
	return [
		ExtractedPage(
			page_number=1,
			content=content,
			content_type="image_description",
			metadata={"width": image.width, "height": image.height},
		)
	]

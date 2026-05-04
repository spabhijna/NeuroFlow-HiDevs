from __future__ import annotations

from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura

from pipelines.ingestion import ExtractedPage


async def _robots_allowed(url: str) -> bool:
	parsed = urlparse(url)
	robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
	parser = RobotFileParser()
	try:
		async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
			response = await client.get(robots_url)
		if response.status_code >= 400:
			return True
		parser.parse(response.text.splitlines())
		return parser.can_fetch("*", url)
	except Exception:
		return True


async def extract_url(url: str) -> list[ExtractedPage]:
	if not await _robots_allowed(url):
		raise ValueError("robots.txt disallows fetching this URL")

	async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
		response = await client.get(url)
		response.raise_for_status()
		html = response.text
		final_url = str(response.url)

	extracted_content = trafilatura.extract(html, include_links=False, include_images=False)
	if not extracted_content:
		extracted_content = trafilatura.extract(html, favor_precision=False) or ""
	metadata_result = trafilatura.extract_metadata(html)
	metadata = {
		"title": metadata_result.title if metadata_result else None,
		"author": metadata_result.author if metadata_result else None,
		"publish_date": metadata_result.date if metadata_result else None,
		"canonical_url": (
			urljoin(final_url, metadata_result.url) if metadata_result and metadata_result.url else final_url
		),
	}
	return [
		ExtractedPage(
			page_number=1,
			content=extracted_content.strip(),
			content_type="text",
			metadata=metadata,
		)
	]

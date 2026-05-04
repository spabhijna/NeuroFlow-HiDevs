from __future__ import annotations

import math
import re
from collections import defaultdict

from pipelines.ingestion import ExtractedPage


def fixed_size_chunk(text: str, size: int = 512) -> list[str]:
	if size <= 0:
		raise ValueError("size must be positive")
	if not text:
		return []
	return [text[i : i + size] for i in range(0, len(text), size)]


def _split_sentences(text: str) -> list[str]:
	sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
	return sentences or ([text.strip()] if text.strip() else [])


def _sentence_embedding_stub(sentence: str, dimensions: int = 8) -> list[float]:
	vector = [0.0] * dimensions
	for idx, token in enumerate(sentence.lower().split()):
		vector[idx % dimensions] += float((hash(token) % 100) / 100.0)
	return vector


def _cosine_similarity(lhs: list[float], rhs: list[float]) -> float:
	dot = sum(l * r for l, r in zip(lhs, rhs))
	left_norm = math.sqrt(sum(l * l for l in lhs))
	right_norm = math.sqrt(sum(r * r for r in rhs))
	if left_norm == 0.0 or right_norm == 0.0:
		return 1.0
	return dot / (left_norm * right_norm)


def semantic_chunk(text: str, threshold: float = 0.7) -> list[str]:
	sentences = _split_sentences(text)
	if len(sentences) <= 1:
		return sentences

	chunks: list[str] = []
	current: list[str] = [sentences[0]]
	prev_embedding = _sentence_embedding_stub(sentences[0])
	for sentence in sentences[1:]:
		current_embedding = _sentence_embedding_stub(sentence)
		similarity = _cosine_similarity(prev_embedding, current_embedding)
		if similarity < threshold and current:
			chunks.append(" ".join(current).strip())
			current = [sentence]
		else:
			current.append(sentence)
		prev_embedding = current_embedding

	if current:
		chunks.append(" ".join(current).strip())
	return chunks


def hierarchical_chunk(
	pages: list[ExtractedPage], size: int = 512
) -> list[tuple[str, dict[str, object]]]:
	sections: dict[str, list[ExtractedPage]] = defaultdict(list)
	for page in pages:
		heading_path = page.metadata.get("heading_path") if page.metadata else None
		section_name = " > ".join(heading_path) if heading_path else "Document"
		sections[section_name].append(page)

	rows: list[tuple[str, dict[str, object]]] = []
	for section, section_pages in sections.items():
		section_text = "\n".join(page.content for page in section_pages if page.content.strip())
		if not section_text:
			continue

		parent_metadata = {
			"relation": "parent",
			"section": section,
		}
		rows.append((section_text[:size], parent_metadata))

		for child_index, child_chunk in enumerate(fixed_size_chunk(section_text, size=size)):
			child_metadata = {
				"relation": "child",
				"parent_section": section,
				"child_index": child_index,
			}
			rows.append((child_chunk, child_metadata))

	return rows

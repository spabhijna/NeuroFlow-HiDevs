def fixed_size_chunk(text: str, size: int = 512) -> list[str]:
	if size <= 0:
		raise ValueError("size must be positive")

	return [text[i:i + size] for i in range(0, len(text), size)]

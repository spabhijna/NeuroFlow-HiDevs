from __future__ import annotations

import pandas as pd

from pipelines.ingestion import ExtractedPage


def _format_numeric_stats(df: pd.DataFrame) -> list[str]:
	lines: list[str] = []
	numeric_columns = df.select_dtypes(include=["number"]).columns
	for column in numeric_columns:
		series = df[column].dropna()
		if series.empty:
			continue
		lines.append(
			f"- {column}: min={series.min()}, max={series.max()}, mean={series.mean()}"
		)
	return lines


def _format_categorical_stats(df: pd.DataFrame) -> list[str]:
	lines: list[str] = []
	categorical_columns = df.select_dtypes(exclude=["number"]).columns
	for column in categorical_columns:
		top_values = df[column].astype(str).value_counts().head(5)
		if top_values.empty:
			continue
		formatted = ", ".join([f"{value} ({count})" for value, count in top_values.items()])
		lines.append(f"- {column}: {formatted}")
	return lines


def extract_csv(file_path: str) -> list[ExtractedPage]:
	df = pd.read_csv(file_path)
	row_count = len(df.index)
	pages: list[ExtractedPage] = []

	if row_count < 1000:
		for offset in range(0, row_count, 100):
			frame = df.iloc[offset : offset + 100]
			content = frame.to_markdown(index=False)
			pages.append(
				ExtractedPage(
					page_number=(offset // 100) + 1,
					content=content,
					content_type="table",
					metadata={"row_start": offset, "row_end": min(offset + 100, row_count)},
				)
			)
		return pages

	column_descriptions = [f"- {col}: {dtype}" for col, dtype in df.dtypes.items()]
	numeric_stats = _format_numeric_stats(df)
	categorical_stats = _format_categorical_stats(df)
	summary = "\n".join(
		[
			"CSV statistical summary",
			"Columns:",
			*column_descriptions,
			"Numeric stats:",
			*(numeric_stats or ["- none"]),
			"Top categorical values:",
			*(categorical_stats or ["- none"]),
		]
	)
	for offset in range(0, row_count, 100):
		pages.append(
			ExtractedPage(
				page_number=(offset // 100) + 1,
				content=summary,
				content_type="table",
				metadata={"row_start": offset, "row_end": min(offset + 100, row_count)},
			)
		)

	return pages

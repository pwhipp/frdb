from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .comparisons import parse_comparisons
from .publication_filters import derive_publication_filters
from .read_excel import read_excel


@dataclass(frozen=True)
class ParsedWorkbook:
    rows: list[dict]
    publication_filters: list[dict]
    comparisons: list[dict[str, str]]


def parse_workbook(path: Path, comparisons_path: Path, comparisons_sheet: str = "Comparisons") -> ParsedWorkbook:
    rows = read_excel(path)
    return ParsedWorkbook(
        rows=rows,
        publication_filters=derive_publication_filters(rows),
        comparisons=parse_comparisons(comparisons_path, rows, comparisons_sheet),
    )

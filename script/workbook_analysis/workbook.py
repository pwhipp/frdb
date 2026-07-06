from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .comparisons import parse_comparisons
from .publication_filters import derive_publication_filters
from .read_excel import read_excel
from .source_workbook import DEFAULT_COMPARISONS_SHEET


@dataclass(frozen=True)
class ParsedWorkbook:
    rows: list[dict]
    publication_filters: list[dict]
    comparisons: list[dict[str, str]]


def parse_workbook(
    path: Path,
    comparisons_sheet: str = DEFAULT_COMPARISONS_SHEET,
    require_all_studies: bool = True,
) -> ParsedWorkbook:
    rows = read_excel(path)
    return ParsedWorkbook(
        rows=rows,
        publication_filters=derive_publication_filters(rows),
        comparisons=parse_comparisons(
            path,
            rows,
            comparisons_sheet,
            require_all_studies=require_all_studies,
        ),
    )

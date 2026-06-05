from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .publication_filters import derive_publication_filters
from .read_excel import read_excel


@dataclass(frozen=True)
class ParsedWorkbook:
    rows: list[dict]
    publication_filters: list[dict]


def parse_workbook(path: Path) -> ParsedWorkbook:
    rows = read_excel(path)
    return ParsedWorkbook(
        rows=rows,
        publication_filters=derive_publication_filters(rows),
    )

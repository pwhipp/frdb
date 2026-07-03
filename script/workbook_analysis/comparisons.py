from __future__ import annotations

from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .read_excel import (
    CellValue,
    OFFICE_REL_NS,
    SPREADSHEET_NS,
    cell_value,
    read_shared_strings,
)
from .rules import clean_text


COMPARISON_SUMMARY_FIELDS = (
    "substrate_class",
    "biological_material_class",
    "better_method_class",
    "worse_method_class",
    "statistical_significance",
)
COMPARISON_DETAIL_FIELDS = (
    "substrate_detail",
    "biological_material_detail",
    "better_recovery_method",
    "worse_recovery_method",
    "comparison_scope",
    "notes_source_result_summary",
)
COMPARISON_FIELDS = (
    "author",
    *COMPARISON_SUMMARY_FIELDS,
    *COMPARISON_DETAIL_FIELDS,
)


def parse_comparisons(
    path: Path,
    publication_rows: list[dict],
    sheet_name: str = "Comparisons",
    require_all_studies: bool = True,
) -> list[dict[str, str]]:
    rows = read_sheet_rows(path, sheet_name)
    validate_comparison_rows(rows, publication_rows, path, sheet_name, require_all_studies)
    return rows


def read_sheet_rows(path: Path, sheet_name: str) -> list[dict[str, str]]:
    with ZipFile(path) as workbook:
        shared_strings = read_shared_strings(workbook)
        worksheet_path = worksheet_path_by_name(workbook, sheet_name)
        worksheet_xml = ET.fromstring(workbook.read(worksheet_path))
        cells = read_worksheet_cells(worksheet_xml, shared_strings)

    table = rows_from_cells(cells)
    if not table:
        return []
    headers = trim_trailing_empty(table[0])
    validate_comparison_headers(headers, path, sheet_name)
    return [dict(zip(headers, row)) for row in table[1:] if any(row)]


def trim_trailing_empty(values: list[str]) -> list[str]:
    trimmed = list(values)
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    return trimmed


def validate_comparison_headers(headers: list[str], path: Path, sheet_name: str) -> None:
    expected = list(COMPARISON_FIELDS)
    if headers != expected:
        raise ValueError(
            f"{path} {sheet_name} sheet columns must be in this exact order: {expected}; found: {headers}"
        )


def worksheet_path_by_name(workbook: ZipFile, sheet_name: str) -> str:
    workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}

    for sheet in workbook_xml.findall(f".//{{{SPREADSHEET_NS}}}sheet"):
        if sheet.attrib.get("name") != sheet_name:
            continue
        rel_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
        target = rel_targets[rel_id].lstrip("/")
        return target if target.startswith("xl/") else f"xl/{target}"

    raise ValueError(f"{workbook.filename} has no {sheet_name!r} worksheet")


def read_worksheet_cells(
    worksheet_xml: ET.Element,
    shared_strings: list[CellValue],
) -> dict[tuple[int, int], str]:
    cells = {}
    for cell in worksheet_xml.findall(f".//{{{SPREADSHEET_NS}}}c"):
        row, column = split_reference(cell.attrib["r"])
        cells[(row, column)] = cell_value(cell, shared_strings).text
    return cells


def rows_from_cells(cells: dict[tuple[int, int], str]) -> list[list[str]]:
    if not cells:
        return []

    max_column = max(column for _, column in cells)
    rows = []
    for row_number in sorted({row for row, _ in cells}):
        row = [clean_text(cells.get((row_number, column), "")) for column in range(1, max_column + 1)]
        rows.append(row)
    return rows


def split_reference(reference: str) -> tuple[int, int]:
    column_letters = "".join(character for character in reference if character.isalpha())
    row_digits = "".join(character for character in reference if character.isdigit())
    if not column_letters or not row_digits:
        raise ValueError(f"Invalid cell reference: {reference}")

    column = 0
    for character in column_letters.upper():
        column = column * 26 + ord(character) - 64
    return int(row_digits), column


def validate_comparison_rows(
    rows: list[dict[str, str]],
    publication_rows: list[dict],
    path: Path,
    sheet_name: str = "Comparisons",
    require_all_studies: bool = True,
) -> None:
    if not rows:
        raise ValueError(f"{path} {sheet_name} sheet has no comparison rows")

    missing_fields = [field for field in COMPARISON_FIELDS if field not in rows[0]]
    if missing_fields:
        raise ValueError(f"{path} {sheet_name} sheet is missing columns: {missing_fields}")

    study_author_counts = Counter(row["authors"] for row in publication_rows)
    duplicate_authors = sorted(author for author, count in study_author_counts.items() if count > 1)
    if duplicate_authors:
        raise ValueError(f"{path} cannot use author as the comparison study reference because the source workbook has duplicate authors: {duplicate_authors}")

    known_authors = set(study_author_counts)
    unknown_authors = sorted({row["author"] for row in rows if row["author"] not in known_authors})
    if unknown_authors:
        raise ValueError(f"{path} contains comparisons for publications not in the source workbook: {unknown_authors}")

    missing_comparisons = sorted(author for author in known_authors if author not in {row["author"] for row in rows})
    if require_all_studies and missing_comparisons:
        raise ValueError(f"{path} is missing comparison rows for source workbook publications: {missing_comparisons}")

    incomplete_rows = [
        f"row {index + 2}: {', '.join(field for field in COMPARISON_FIELDS if not row.get(field))}"
        for index, row in enumerate(rows)
        if any(not row.get(field) for field in COMPARISON_FIELDS)
    ]
    if incomplete_rows:
        raise ValueError(f"{path} {sheet_name} sheet has incomplete rows: {incomplete_rows[:10]}")

    row_keys = [tuple(row[field] for field in COMPARISON_FIELDS) for row in rows]
    duplicate_rows = [f"row {index + 2}" for index, key in enumerate(row_keys) if row_keys.count(key) > 1]
    if duplicate_rows:
        raise ValueError(f"{path} {sheet_name} sheet has duplicate comparison rows: {duplicate_rows[:10]}")

from __future__ import annotations

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


COMPARISON_FIELDS = (
    "source_excel_row",
    "author",
    "substrate_class",
    "substrate_detail",
    "biological_material_class",
    "biological_material_detail",
    "better_recovery_method",
    "better_method_class",
    "worse_recovery_method",
    "worse_method_class",
    "statistical_significance",
    "comparison_scope",
    "notes_source_result_summary",
)


def parse_comparisons(path: Path, publication_rows: list[dict]) -> list[dict[str, str]]:
    rows = read_sheet_rows(path, "Comparisons")
    validate_comparison_rows(rows, publication_rows, path)
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
    headers = table[0]
    return [dict(zip(headers, row)) for row in table[1:] if any(row)]


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


def validate_comparison_rows(rows: list[dict[str, str]], publication_rows: list[dict], path: Path) -> None:
    if not rows:
        raise ValueError(f"{path} Comparisons sheet has no comparison rows")

    missing_fields = [field for field in COMPARISON_FIELDS if field not in rows[0]]
    if missing_fields:
        raise ValueError(f"{path} Comparisons sheet is missing columns: {missing_fields}")

    source_row_by_author = {row["authors"]: str(index + 2) for index, row in enumerate(publication_rows)}
    unknown_authors = sorted({row["author"] for row in rows if row["author"] not in source_row_by_author})
    if unknown_authors:
        raise ValueError(f"{path} contains comparisons for publications not in the source workbook: {unknown_authors}")

    stale_rows = []
    for row in rows:
        expected_source_row = source_row_by_author[row["author"]]
        if row["source_excel_row"] != expected_source_row:
            stale_rows.append(f"{row['author']} expected {expected_source_row}, found {row['source_excel_row']}")
    if stale_rows:
        raise ValueError(f"{path} source_excel_row values are stale: {stale_rows[:10]}")

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .rules import (
    HEADER_FIELDS,
    REQUIRED_FIELDS,
    canonical_biological_material,
    canonical_equipment,
    canonical_recovery_methods,
    canonical_substrate_types,
    clean_text,
    normalise_header,
    replicate_band_key,
)


SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"main": SPREADSHEET_NS, "rel": PACKAGE_REL_NS}


@dataclass(frozen=True)
class CellValue:
    text: str


def parse_workbook(path: Path) -> list[dict]:
    with ZipFile(path) as workbook:
        shared_strings = read_shared_strings(workbook)
        workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
        worksheet_path = first_worksheet_path(workbook, workbook_xml)
        worksheet_xml = ET.fromstring(workbook.read(worksheet_path))
        style_fill_ids = read_style_fill_ids(workbook)
        hyperlinks = read_hyperlinks(workbook, worksheet_path, worksheet_xml)
        cells, cell_styles = read_cells(worksheet_xml, shared_strings)

    header_row = find_header_row(cells)
    column_fields = fields_by_column(cells, header_row)
    replicate_bands = replicate_band_lookup(cells, cell_styles, style_fill_ids)
    return build_rows(cells, cell_styles, hyperlinks, replicate_bands, style_fill_ids, header_row, column_fields)


def read_shared_strings(workbook: ZipFile) -> list[CellValue]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []

    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    return [shared_string_value(item) for item in root.findall("main:si", {"main": SPREADSHEET_NS})]


def shared_string_value(item: ET.Element) -> CellValue:
    runs = item.findall("main:r", {"main": SPREADSHEET_NS})
    if not runs:
        text = clean_text("".join(node.text or "" for node in item.findall(".//main:t", {"main": SPREADSHEET_NS})))
        return CellValue(text=text)

    text_parts = []
    for run in runs:
        run_text = clean_text("".join(node.text or "" for node in run.findall("main:t", {"main": SPREADSHEET_NS})))
        if not run_text:
            continue
        text_parts.append(run_text)

    return CellValue(text="".join(text_parts))


def first_worksheet_path(workbook: ZipFile, workbook_xml: ET.Element) -> str:
    rels = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", NS)
    }
    sheet = workbook_xml.find("main:sheets/main:sheet", {"main": SPREADSHEET_NS})
    if sheet is None:
        raise ValueError("Workbook has no worksheets")
    rel_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
    target = rel_targets[rel_id].lstrip("/")
    return target if target.startswith("xl/") else f"xl/{target}"


def read_style_fill_ids(workbook: ZipFile) -> list[int]:
    styles_xml = ET.fromstring(workbook.read("xl/styles.xml"))
    return [
        int(style.attrib.get("fillId", "0"))
        for style in styles_xml.findall("main:cellXfs/main:xf", {"main": SPREADSHEET_NS})
    ]


def read_hyperlinks(workbook: ZipFile, worksheet_path: str, worksheet_xml: ET.Element) -> dict[str, str]:
    rel_path = str(Path(worksheet_path).parent / "_rels" / f"{Path(worksheet_path).name}.rels")
    if rel_path not in workbook.namelist():
        return {}

    rels = ET.fromstring(workbook.read(rel_path))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", NS)
        if rel.attrib.get("Type", "").endswith("/hyperlink")
    }

    links: dict[str, str] = {}
    for hyperlink in worksheet_xml.findall(".//main:hyperlink", {"main": SPREADSHEET_NS}):
        rel_id = hyperlink.attrib.get(f"{{{OFFICE_REL_NS}}}id")
        if not rel_id or rel_id not in targets:
            continue
        for cell_ref in expand_cell_range(hyperlink.attrib["ref"]):
            links[cell_ref] = targets[rel_id]
    return links


def read_cells(
    worksheet_xml: ET.Element,
    shared_strings: list[CellValue],
) -> tuple[dict[str, CellValue], dict[str, int]]:
    cells: dict[str, CellValue] = {}
    styles: dict[str, int] = {}

    for cell in worksheet_xml.findall(".//main:c", {"main": SPREADSHEET_NS}):
        reference = cell.attrib["r"]
        styles[reference] = int(cell.attrib.get("s", "0"))
        cells[reference] = cell_value(cell, shared_strings)

    return cells, styles


def cell_value(cell: ET.Element, shared_strings: list[CellValue]) -> CellValue:
    cell_type = cell.attrib.get("t")
    value_node = cell.find("main:v", {"main": SPREADSHEET_NS})

    if cell_type == "s" and value_node is not None:
        return shared_strings[int(value_node.text or "0")]

    if cell_type == "inlineStr":
        text = clean_text("".join(node.text or "" for node in cell.findall(".//main:t", {"main": SPREADSHEET_NS})))
        return CellValue(text=text)

    text = clean_text(value_node.text if value_node is not None else "")
    return CellValue(text=text)


def find_header_row(cells: dict[str, CellValue]) -> int:
    rows = {split_cell_reference(reference)[1] for reference in cells}
    for row_number in sorted(rows):
        headers = {
            normalise_header(cell.text)
            for reference, cell in cells.items()
            if split_cell_reference(reference)[1] == row_number
        }
        if "authors" in headers and "results" in headers:
            return row_number
    raise ValueError("Could not locate a header row containing Authors and Results")


def fields_by_column(cells: dict[str, CellValue], header_row: int) -> dict[str, str]:
    column_fields = {}
    for reference, cell in cells.items():
        column, row_number = split_cell_reference(reference)
        if row_number != header_row:
            continue
        field = HEADER_FIELDS.get(normalise_header(cell.text))
        if field:
            column_fields[column] = field

    missing = [field for field in REQUIRED_FIELDS if field not in column_fields.values()]
    if missing:
        raise ValueError(f"Workbook is missing required columns: {', '.join(missing)}")
    return column_fields


def replicate_band_lookup(
    cells: dict[str, CellValue],
    cell_styles: dict[str, int],
    style_fill_ids: list[int],
) -> dict[int, str]:
    lookup: dict[int, str] = {}
    for reference in ("M1", "N1", "O1"):
        if reference not in cell_styles:
            continue
        fill_id = style_fill_ids[cell_styles[reference]]
        lookup[fill_id] = cells[reference].text.rstrip(".")
    return lookup


def build_rows(
    cells: dict[str, CellValue],
    cell_styles: dict[str, int],
    hyperlinks: dict[str, str],
    replicate_bands: dict[int, str],
    style_fill_ids: list[int],
    header_row: int,
    column_fields: dict[str, str],
) -> list[dict]:
    rows = []
    row_number = header_row + 1
    authors_column = column_for_field(column_fields, "authors")
    statistical_column = column_for_field(column_fields, "statistical_analysis")

    while cells.get(f"{authors_column}{row_number}", CellValue("")).text:
        row = {}
        for column, key in column_fields.items():
            cell = cells.get(f"{column}{row_number}", CellValue(""))
            row[key] = cell.text

        author_reference = f"{authors_column}{row_number}"
        row["source_url"] = hyperlinks.get(author_reference, "")
        row["recovery_methods_filter"] = canonical_recovery_methods(row["recovery_methods"])
        row["equipment_tested_filter"] = canonical_equipment(row["equipment_tested"], row["recovery_methods"])
        row["biological_material_filter"] = canonical_biological_material(row["biological_material"])
        row["substrate_type_filter"] = canonical_substrate_types(row["substrate_type"])

        statistical_reference = f"{statistical_column}{row_number}"
        fill_id = style_fill_ids[cell_styles.get(statistical_reference, 0)]
        row["replicate_band"] = replicate_bands.get(fill_id, "")
        row["replicate_band_key"] = replicate_band_key(row["replicate_band"])

        rows.append(row)
        row_number += 1

    return rows


def column_for_field(column_fields: dict[str, str], field: str) -> str:
    for column, mapped_field in column_fields.items():
        if mapped_field == field:
            return column
    raise ValueError(f"Missing column for {field}")


def expand_cell_range(reference: str) -> list[str]:
    if ":" not in reference:
        return [reference]

    start, end = reference.split(":", 1)
    start_column, start_row = split_cell_reference(start)
    end_column, end_row = split_cell_reference(end)
    if start_column != end_column:
        return [reference]
    return [f"{start_column}{row}" for row in range(start_row, end_row + 1)]


def split_cell_reference(reference: str) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)", reference)
    if not match:
        raise ValueError(f"Invalid cell reference: {reference}")
    return match.group(1), int(match.group(2))

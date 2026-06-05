from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import re

from data.files import (
    FILTERS_JSON,
    FILTER_HIGHLIGHT_TERMS_JSON,
    PUBLICATION_FILTERS_JSON,
    PUBLICATIONS_JSON,
    data_dir,
)

from .rules import (
    BIOLOGICAL_MATERIAL_ORDER,
    EQUIPMENT_ORDER,
    FILTER_HIGHLIGHT_TERMS,
    RECOVERY_METHOD_ORDER,
    SUBSTRATE_TYPE_ORDER,
)


def default_output_folder(repo_root: Path) -> Path:
    return data_dir(repo_root)


def module_name_from_stem(stem: str) -> str:
    name = re.sub(r"\W+", "_", stem.lower()).strip("_")
    if not name:
        raise ValueError("Workbook name does not contain a usable module name")
    if name[0].isdigit():
        name = f"workbook_{name}"
    return name


def merge_existing_rows(output_folder: Path, workbook_path: Path, generated_rows: list[dict]) -> list[dict]:
    existing_rows = load_existing_rows(output_folder, workbook_path)
    existing_by_key = {}
    for row in existing_rows:
        if row.get("authors"):
            existing_by_key[row["authors"]] = row
    next_id = max((row.get("id", 0) for row in existing_rows), default=0) + 1
    merged = []

    for row in generated_rows:
        existing = existing_by_key.get(row["authors"])
        if existing:
            row["id"] = existing["id"]
        else:
            row["id"] = next_id
            next_id += 1
        merged.append(row)

    return sorted(merged, key=lambda item: item["id"])


def load_existing_rows(output_folder: Path, workbook_path: Path) -> list[dict]:
    publications_path = output_folder / PUBLICATIONS_JSON
    if publications_path.exists():
        return list(json.loads(publications_path.read_text(encoding="utf-8")))

    legacy_path = output_folder / f"{module_name_from_stem(workbook_path.stem)}.py"
    if legacy_path.exists():
        return load_legacy_rows(legacy_path)

    return []


def load_legacy_rows(path: Path) -> list[dict]:
    spec = spec_from_file_location("_frdb_existing_data", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load existing data module: {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(getattr(module, "ROWS", []))


def write_analysis_json(output_folder: Path, rows: list[dict], compact: bool) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    filter_options = filters()
    publication_rows, publication_filters = split_publication_filters(rows, tuple(filter_options))
    write_json(output_folder / PUBLICATIONS_JSON, publication_rows, compact)
    write_json(output_folder / PUBLICATION_FILTERS_JSON, publication_filters, compact)
    write_json(output_folder / FILTERS_JSON, filter_options, compact)
    write_json(output_folder / FILTER_HIGHLIGHT_TERMS_JSON, FILTER_HIGHLIGHT_TERMS, compact)


def write_json(path: Path, value, compact: bool) -> None:
    path.write_text(f"{json_text(value, compact)}\n", encoding="utf-8")


def json_text(value, compact: bool) -> str:
    if compact:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, indent=4)


def filters() -> dict[str, list[str]]:
    return {
        "recovery_methods": list(RECOVERY_METHOD_ORDER),
        "equipment_tested": list(EQUIPMENT_ORDER),
        "biological_material": list(BIOLOGICAL_MATERIAL_ORDER),
        "substrate_type": list(SUBSTRATE_TYPE_ORDER),
    }


def split_publication_filters(rows: list[dict], filter_fields: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    filter_source_fields = {f"{field}_filter" for field in filter_fields}
    publication_rows = []
    publication_filters = []

    for row in rows:
        publication_rows.append({key: value for key, value in row.items() if key not in filter_source_fields})
        publication_filters.append({
            "authors": row["authors"],
            **{field: row[f"{field}_filter"] for field in filter_fields},
        })

    return publication_rows, publication_filters

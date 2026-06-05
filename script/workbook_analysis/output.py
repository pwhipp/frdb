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

from .publication_filters import available_filter_values
from .rules import FILTER_HIGHLIGHT_TERMS


def default_output_folder(repo_root: Path) -> Path:
    return data_dir(repo_root)


def legacy_module_name(stem: str) -> str:
    name = re.sub(r"\W+", "_", stem.lower()).strip("_")
    if not name:
        raise ValueError("Workbook name does not contain a usable module name")
    if name[0].isdigit():
        name = f"workbook_{name}"
    return name


def assign_publication_ids(output_folder: Path, workbook_path: Path, rows: list[dict]) -> list[dict]:
    existing_rows = load_existing_rows(output_folder, workbook_path)
    existing_by_author = {}
    for row in existing_rows:
        if row.get("authors"):
            existing_by_author[row["authors"]] = row
    next_id = max((row.get("id", 0) for row in existing_rows), default=0) + 1
    assigned_rows = []

    for row in rows:
        existing = existing_by_author.get(row["authors"])
        if existing:
            row["id"] = existing["id"]
        else:
            row["id"] = next_id
            next_id += 1
        assigned_rows.append(row)

    return sorted(assigned_rows, key=lambda item: item["id"])


def load_existing_rows(output_folder: Path, workbook_path: Path) -> list[dict]:
    publications_path = output_folder / PUBLICATIONS_JSON
    if publications_path.exists():
        return list(json.loads(publications_path.read_text(encoding="utf-8")))

    legacy_path = output_folder / f"{legacy_module_name(workbook_path.stem)}.py"
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


def write_data_files(output_folder: Path, rows: list[dict], publication_filters: list[dict], compact: bool) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    write_json(output_folder / PUBLICATIONS_JSON, rows, compact)
    write_json(output_folder / PUBLICATION_FILTERS_JSON, publication_filters_in_row_order(rows, publication_filters), compact)
    write_json(output_folder / FILTERS_JSON, available_filter_values(), compact)
    write_json(output_folder / FILTER_HIGHLIGHT_TERMS_JSON, FILTER_HIGHLIGHT_TERMS, compact)


def write_json(path: Path, value, compact: bool) -> None:
    path.write_text(f"{json_text(value, compact)}\n", encoding="utf-8")


def json_text(value, compact: bool) -> str:
    if compact:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, indent=4)


def publication_filters_in_row_order(rows: list[dict], publication_filters: list[dict]) -> list[dict]:
    publication_filters_by_author = {
        publication_filter["authors"]: publication_filter
        for publication_filter in publication_filters
    }
    try:
        return [publication_filters_by_author[row["authors"]] for row in rows]
    except KeyError as error:
        raise ValueError(f"Missing publication filters for {error.args[0]}") from error

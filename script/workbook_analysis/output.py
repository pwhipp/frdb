from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import re

from data.files import (
    DECISION_MAP_JSON,
    FILTERS_JSON,
    FILTER_HIGHLIGHT_TERMS_JSON,
    PUBLICATION_FILTERS_JSON,
    PUBLICATIONS_JSON,
    TABLES_JSON,
    data_dir,
)

from .comparisons import COMPARISON_FIELDS
from .decision_map import build_decision_map
from .publication_filters import available_filter_values
from .rules import FILTER_HIGHLIGHT_TERMS


def table_columns(fields, frozen: set[str] | None = None) -> list[dict]:
    frozen = frozen or set()
    return [
        {
            "title": title_for_field(field),
            "field": field,
            "width": width_for_field(field),
            "frozen": field in frozen,
            **formatter_for_field(field),
        }
        for field in fields
    ]


def formatter_for_field(field: str) -> dict:
    if field == "score_contribution_summary":
        return {"formatter": "score_contribution"}
    return {}


def author_link_column(field: str, title: str = "Author") -> dict:
    return {
        "title": title,
        "field": field,
        "width": width_for_field(field),
        "frozen": True,
        "formatter": "publication_link",
    }


def title_for_field(field: str) -> str:
    if field == "score_contribution_summary":
        return "Score contribution"
    return field.replace("_", " ").title()


def width_for_field(field: str) -> int:
    if field in {"results", "trace_notes", "notes_source_result_summary", "confidence_rationale", "requested_method_ranking", "ranking_with_unspecified_swab_bucket", "mapping_rule", "score_effect"}:
        return 680
    if field in {"author", "authors", "supporting_authors"}:
        return 240
    if "method" in field or "scope" in field or "detail" in field:
        return 280
    if field == "score_contribution_summary":
        return 220
    return 150


PUBLICATION_COLUMNS = [
    {"title": "Authors", "field": "authors", "width": 185, "frozen": True, "formatter": "authors"},
    {"title": "No. of samples", "field": "sample_count", "width": 125},
    {"title": "Recovery methods", "field": "recovery_methods", "width": 185, "filterable": True},
    {"title": "Equipment tested", "field": "equipment_tested", "width": 280, "filterable": True},
    {"title": "Biological material", "field": "biological_material", "width": 190, "filterable": True},
    {"title": "Substrate type", "field": "substrate_type", "width": 150, "filterable": True},
    {"title": "Substrate descriptions", "field": "substrate_descriptions", "width": 280},
    {"title": "Statistical analysis", "field": "statistical_analysis", "width": 160, "formatter": "statistical"},
    {"title": "STR analysis", "field": "str_analysis", "width": 115},
    {"title": "Results", "field": "results", "width": 820},
]
VISIBLE_COMPARISON_FIELDS = tuple(field for field in COMPARISON_FIELDS if field != "source_excel_row")
SCORED_COMPARISON_FIELDS = (
    *VISIBLE_COMPARISON_FIELDS,
    "decision_bio",
    "decision_surface",
    "normalized_better_methods",
    "normalized_worse_methods",
    "normalized_tie_methods",
    "score_contribution_summary",
)

TABLE_CATALOG = [
    {"id": "publications", "label": "Publications", "description": "Source publication rows from the interactive evidence workbook.", "columns": PUBLICATION_COLUMNS, "special_filters": True},
    {"id": "recovery_comparisons", "label": "Recovery comparisons", "description": "Curated method-comparison rows used as decision-map source evidence.", "columns": [author_link_column("author"), *table_columns(tuple(field for field in VISIBLE_COMPARISON_FIELDS if field != "author"))]},
    {"id": "decision_cells", "label": "Decision cells", "description": "Long-form decision-map cells by biological material and surface.", "columns": table_columns(("biological_material", "surface", "top_requested_method", "confidence", "unique_studies_requested_methods", "unique_studies_including_unspecified_swab", "requested_method_ranking", "ranking_with_unspecified_swab_bucket", "confidence_rationale"), frozen={"biological_material", "surface"})},
    {"id": "technique_rankings", "label": "Technique rankings", "description": "Scored technique rankings for each decision cell.", "columns": table_columns(("biological_material", "surface", "method", "score", "unique_studies", "comparison_contributions", "wins", "losses", "ties", "significant_wins", "significant_losses", "supporting_authors", "trace_notes"), frozen={"biological_material", "surface", "method"})},
    {"id": "scored_comparisons", "label": "Scored comparisons", "description": "Trace table showing how each comparison row contributes to the decision map.", "columns": [author_link_column("author"), *table_columns(tuple(field for field in SCORED_COMPARISON_FIELDS if field != "author"))]},
    {"id": "method_normalization", "label": "Method normalization", "description": "Normalization rules used before scoring.", "columns": table_columns(("normalized_method", "mapping_rule", "aggregation_note"), frozen={"normalized_method"})},
    {"id": "scoring_readme", "label": "Scoring rules", "description": "Scoring and confidence rules used by the decision map.", "columns": table_columns(("rule", "score_effect"), frozen={"rule"})},
]


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


def write_data_files(output_folder: Path, rows: list[dict], publication_filters: list[dict], comparisons: list[dict[str, str]], compact: bool) -> None:
    decision_map = build_decision_map(comparisons, rows)
    output_folder.mkdir(parents=True, exist_ok=True)
    write_json(output_folder / PUBLICATIONS_JSON, rows, compact)
    write_json(output_folder / PUBLICATION_FILTERS_JSON, publication_filters_in_row_order(rows, publication_filters), compact)
    write_json(output_folder / FILTERS_JSON, available_filter_values(), compact)
    write_json(output_folder / FILTER_HIGHLIGHT_TERMS_JSON, FILTER_HIGHLIGHT_TERMS, compact)
    write_json(output_folder / DECISION_MAP_JSON, decision_map, compact)
    write_json(output_folder / TABLES_JSON, build_tables_payload(comparisons, decision_map, rows), compact)


def build_tables_payload(comparisons: list[dict[str, str]], decision_map: dict, publications: list[dict]) -> dict:
    return {
        "catalog": TABLE_CATALOG,
        "tables": {
            "recovery_comparisons": comparison_table_rows(comparisons, publications),
            "decision_cells": decision_cell_rows(decision_map["cells"]),
            "technique_rankings": strip_private_fields(decision_map["technique_rankings"]),
            "scored_comparisons": strip_table_internal_fields(decision_map["scored_comparisons"]),
            "method_normalization": decision_map["method_normalization"],
            "scoring_readme": decision_map["scoring_readme"],
        },
    }


def decision_cell_rows(cells: list[dict]) -> list[dict]:
    rows = []
    for cell in cells:
        rows.append({
            "biological_material": cell["biological_material"],
            "surface": cell["surface"],
            "top_requested_method": cell["top_requested_method"],
            "confidence": cell["confidence"],
            "unique_studies_requested_methods": cell["unique_studies_requested_methods"],
            "unique_studies_including_unspecified_swab": cell["unique_studies_including_unspecified_swab"],
            "requested_method_ranking": ranking_text(cell["rankings"]),
            "ranking_with_unspecified_swab_bucket": ranking_text(cell["ranking_with_unspecified_swab_bucket"]),
            "confidence_rationale": cell["confidence_rationale"],
        })
    return rows


def ranking_text(rankings: list[dict]) -> str:
    if not rankings:
        return "No direct target-method evidence."
    return "\n".join(
        f"{item['rank']}. {item['method']} (score {item['score']:+.2f}; studies {item['unique_studies']}; wins/losses/ties {item['wins']}/{item['losses']}/{item['ties']}; sig wins/losses {item['significant_wins']}/{item['significant_losses']})"
        for item in rankings
    )


def strip_private_fields(rows: list[dict]) -> list[dict]:
    return [{key: value for key, value in row.items() if key != "publication_ids"} for row in rows]


def strip_table_internal_fields(rows: list[dict]) -> list[dict]:
    return [
        {key: value for key, value in row.items() if key not in {"publication_ids", "source_excel_row"}}
        for row in rows
    ]


def comparison_table_rows(comparisons: list[dict[str, str]], publications: list[dict]) -> list[dict]:
    publication_id_by_author = {publication["authors"]: publication["id"] for publication in publications}
    rows = []
    for comparison in comparisons:
        rows.append({
            key: value
            for key, value in {
                **comparison,
                "publication_id": publication_id_by_author[comparison["author"]],
            }.items()
            if key != "source_excel_row"
        })
    return rows


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

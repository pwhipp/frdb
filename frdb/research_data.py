from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from data.files import (
    DECISION_MAP_JSON,
    FILTERS_JSON,
    FILTER_HIGHLIGHT_TERMS_JSON,
    PUBLICATION_FILTERS_JSON,
    PUBLICATIONS_JSON,
    TABLES_JSON,
    data_dir,
)


DATA_DIR = data_dir(Path(__file__).resolve().parent.parent)
PUBLICATIONS_PATH = DATA_DIR / PUBLICATIONS_JSON
PUBLICATION_FILTERS_PATH = DATA_DIR / PUBLICATION_FILTERS_JSON
FILTERS_PATH = DATA_DIR / FILTERS_JSON
FILTER_HIGHLIGHT_TERMS_PATH = DATA_DIR / FILTER_HIGHLIGHT_TERMS_JSON
DECISION_MAP_PATH = DATA_DIR / DECISION_MAP_JSON
TABLES_PATH = DATA_DIR / TABLES_JSON


@lru_cache(maxsize=1)
def load_research_data() -> dict:
    rows = load_json(PUBLICATIONS_PATH)
    filters = load_json(FILTERS_PATH)
    publication_filters = load_json(PUBLICATION_FILTERS_PATH)
    allowed_filter_values = {field: set(values) for field, values in filters.items()}
    validate_publication_filter_links(rows, publication_filters, allowed_filter_values)
    return {
        "rows": rows,
        "filters": filters,
        "publication_filters": publication_filters,
    }


@lru_cache(maxsize=1)
def load_filter_highlight_terms() -> dict:
    return load_json(FILTER_HIGHLIGHT_TERMS_PATH)


@lru_cache(maxsize=1)
def load_decision_map() -> dict:
    return load_json(DECISION_MAP_PATH)


@lru_cache(maxsize=1)
def load_tables_data() -> dict:
    return load_json(TABLES_PATH)


def load_table_catalog() -> list[dict]:
    return load_tables_data()["catalog"]


def load_table_data(table_id: str) -> dict:
    table = table_metadata(table_id)
    payload = {"table": table, "rows": rows_for_table(table_id)}
    if table.get("special_filters"):
        research_data = load_research_data()
        payload["filters"] = research_data["filters"]
        payload["publication_filters"] = research_data["publication_filters"]
    return payload


def table_metadata(table_id: str) -> dict:
    for table in load_table_catalog():
        if table["id"] == table_id:
            return table
    raise ValueError(f"Unknown table: {table_id}")


def rows_for_table(table_id: str) -> list[dict]:
    if table_id == "publications":
        return load_research_data()["rows"]
    tables = load_tables_data()["tables"]
    if table_id not in tables:
        raise ValueError(f"Unknown table: {table_id}")
    return tables[table_id]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_publication_filter_links(
    rows: list[dict],
    publication_filters: list[dict],
    allowed_filter_values: dict[str, set[str]],
) -> None:
    filter_fields = tuple(allowed_filter_values)
    publication_authors = authors_set(rows, PUBLICATIONS_JSON)
    filter_authors = authors_set(publication_filters, PUBLICATION_FILTERS_JSON)
    if publication_authors != filter_authors:
        missing = sorted(publication_authors - filter_authors)
        extra = sorted(filter_authors - publication_authors)
        raise ValueError(
            f"{PUBLICATION_FILTERS_JSON} author links do not match {PUBLICATIONS_JSON}: "
            f"missing={missing}, extra={extra}"
        )

    allowed_fields = {"authors", *filter_fields}
    for publication_filter in publication_filters:
        fields = set(publication_filter)
        missing_fields = set(filter_fields) - fields
        extra_fields = fields - allowed_fields
        if missing_fields or extra_fields:
            raise ValueError(
                f"{PUBLICATION_FILTERS_JSON} has malformed filter row for "
                f"{publication_filter.get('authors', '<missing authors>')}: "
                f"missing={sorted(missing_fields)}, extra={sorted(extra_fields)}"
            )
        validate_publication_filter_values(publication_filter, allowed_filter_values)


def validate_publication_filter_values(
    publication_filter: dict,
    allowed_filter_values: dict[str, set[str]],
) -> None:
    for field, allowed_values in allowed_filter_values.items():
        values = publication_filter[field]
        if not isinstance(values, list):
            raise ValueError(
                f"{PUBLICATION_FILTERS_JSON} field {field} for "
                f"{publication_filter['authors']} must be a list"
            )
        unknown_values = sorted(set(values) - allowed_values)
        if unknown_values:
            raise ValueError(
                f"{PUBLICATION_FILTERS_JSON} field {field} for "
                f"{publication_filter['authors']} contains unknown values: {unknown_values}"
            )


def authors_set(rows: list[dict], source_name: str) -> set[str]:
    authors = [row.get("authors") for row in rows]
    missing_count = sum(1 for author in authors if not author)
    if missing_count:
        raise ValueError(f"{source_name} has {missing_count} rows without authors")

    author_counts = Counter(authors)
    duplicates = sorted(author for author, count in author_counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"{source_name} has duplicate authors links: {duplicates}")
    return set(authors)

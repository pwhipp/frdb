from __future__ import annotations

from functools import lru_cache
import importlib
import pkgutil

import data as generated_data


FILTER_FIELDS = ("recovery_methods", "equipment_tested", "biological_material", "substrate_type")


@lru_cache(maxsize=1)
def load_research_data() -> dict:
    rows = []
    filters = {field: [] for field in FILTER_FIELDS}

    for module in generated_data_modules():
        rows.extend(module_rows(module, len(rows)))
        merge_filters(filters, getattr(module, "FILTERS", {}))

    return {
        "rows": rows,
        "filters": filters,
    }


def generated_data_modules() -> list:
    modules = []
    for module_info in pkgutil.iter_modules(generated_data.__path__):
        if module_info.name.startswith("_"):
            continue
        modules.append(importlib.import_module(f"{generated_data.__name__}.{module_info.name}"))
    return modules


def module_rows(module, offset: int) -> list[dict]:
    rows = []
    for index, row in enumerate(getattr(module, "ROWS", []), start=1):
        display_row = dict(row)
        display_row["id"] = offset + index
        rows.append(display_row)
    return rows


def merge_filters(filters: dict[str, list[str]], module_filters: dict[str, list[str]]) -> None:
    for field in FILTER_FIELDS:
        known = set(filters[field])
        for value in module_filters.get(field, []):
            if value not in known:
                filters[field].append(value)
                known.add(value)

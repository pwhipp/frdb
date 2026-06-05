from __future__ import annotations

from .rules import (
    BIOLOGICAL_MATERIAL_ORDER,
    EQUIPMENT_ORDER,
    RECOVERY_METHOD_ORDER,
    SUBSTRATE_TYPE_ORDER,
    canonical_biological_material,
    canonical_equipment,
    canonical_recovery_methods,
    canonical_substrate_types,
)


def available_filter_values() -> dict[str, list[str]]:
    return {
        "recovery_methods": list(RECOVERY_METHOD_ORDER),
        "equipment_tested": list(EQUIPMENT_ORDER),
        "biological_material": list(BIOLOGICAL_MATERIAL_ORDER),
        "substrate_type": list(SUBSTRATE_TYPE_ORDER),
    }


def derive_publication_filters(rows: list[dict]) -> list[dict]:
    return [derive_publication_filter(row) for row in rows]


def derive_publication_filter(row: dict) -> dict:
    return {
        "authors": row["authors"],
        "recovery_methods": canonical_recovery_methods(row["recovery_methods"], row["equipment_tested"]),
        "equipment_tested": canonical_equipment(row["equipment_tested"], row["recovery_methods"]),
        "biological_material": canonical_biological_material(row["biological_material"]),
        "substrate_type": canonical_substrate_types(row["substrate_type"]),
    }

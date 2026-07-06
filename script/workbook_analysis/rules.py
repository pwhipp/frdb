from __future__ import annotations

from functools import lru_cache
import re
from typing import Iterable

from .rule_definitions import (
    BIOLOGICAL_MATERIAL_DEFINITIONS,
    EQUIPMENT_DEFINITIONS,
    FILTER_DEFINITIONS,
    HEADER_FIELDS,
    RECOVERY_METHOD_DEFINITIONS,
    RuleDefinition,
    SUBSTRATE_TYPE_DEFINITIONS,
    SWAB_METHOD_LABELS,
    SWAB_RECOVERY_TRIGGER_TERMS,
    SWAB_UNSPECIFIED_LABEL,
)


REQUIRED_FIELDS = tuple(HEADER_FIELDS.values())


def _highlight_terms(definition: RuleDefinition) -> tuple[str, ...]:
    return definition.highlight_terms or definition.match_terms


@lru_cache(maxsize=1)
def build_filter_highlight_terms() -> dict[str, dict[str, list[str]]]:
    return {
        field: {
            definition.label: list(_highlight_terms(definition))
            for definition in definitions
        }
        for field, definitions in FILTER_DEFINITIONS.items()
    }


_RECOVERY_METHOD_BY_LABEL = {
    definition.label: definition
    for definition in RECOVERY_METHOD_DEFINITIONS
}
_SWAB_METHOD_DEFINITIONS = tuple(
    _RECOVERY_METHOD_BY_LABEL[label]
    for label in SWAB_METHOD_LABELS
)

RECOVERY_METHOD_ORDER = tuple(definition.label for definition in RECOVERY_METHOD_DEFINITIONS)
TAPE_LIFT_TOKENS = _RECOVERY_METHOD_BY_LABEL["Tape lift"].match_terms
MOIST_SWAB_TOKENS = _RECOVERY_METHOD_BY_LABEL["Moist swab"].match_terms
WET_SWAB_TOKENS = _RECOVERY_METHOD_BY_LABEL["Wet swab"].match_terms
WET_SWAB_ABBREVIATIONS = _RECOVERY_METHOD_BY_LABEL["Wet swab"].whole_word_terms
WET_DRY_SWAB_TOKENS = _RECOVERY_METHOD_BY_LABEL["Wet-dry swab"].match_terms
WET_DRY_SWAB_ABBREVIATIONS = _RECOVERY_METHOD_BY_LABEL["Wet-dry swab"].whole_word_terms
OTHER_RECOVERY_METHOD_TOKENS = _RECOVERY_METHOD_BY_LABEL["Other"].match_terms

EQUIPMENT_RULES = tuple((definition.label, definition.match_terms) for definition in EQUIPMENT_DEFINITIONS)
EQUIPMENT_ORDER = tuple(definition.label for definition in EQUIPMENT_DEFINITIONS)

BIOLOGICAL_MATERIAL_RULES = tuple(
    (definition.label, definition.match_terms)
    for definition in BIOLOGICAL_MATERIAL_DEFINITIONS
)
BIOLOGICAL_MATERIAL_ORDER = tuple(definition.label for definition in BIOLOGICAL_MATERIAL_DEFINITIONS)
SUBSTRATE_TYPE_ORDER = tuple(definition.label for definition in SUBSTRATE_TYPE_DEFINITIONS)
FILTER_HIGHLIGHT_TERMS = build_filter_highlight_terms()


def canonical_recovery_methods(recovery_methods: str, equipment: str) -> list[str]:
    recovery_content = normalise_for_matching(recovery_methods)
    content = normalise_for_matching(f"{recovery_methods}\n{equipment}")
    matches = []
    if contains_any(content, TAPE_LIFT_TOKENS):
        matches.append("Tape lift")
    if contains_any(content, SWAB_RECOVERY_TRIGGER_TERMS):
        matches.extend(canonical_swab_methods(content))
    if contains_any(recovery_content, OTHER_RECOVERY_METHOD_TOKENS):
        matches.append("Other")
    if not matches and recovery_content:
        matches.append("Other")
    return ordered_unique(matches, RECOVERY_METHOD_ORDER)


def canonical_swab_methods(content: str) -> list[str]:
    methods = []
    for definition in _SWAB_METHOD_DEFINITIONS:
        if contains_any(content, definition.match_terms) or contains_abbreviation(
            content,
            definition.whole_word_terms,
        ):
            methods.append(definition.label)
    return methods or [SWAB_UNSPECIFIED_LABEL]


def canonical_equipment(equipment: str, recovery_methods: str) -> list[str]:
    content = normalise_for_matching(f"{equipment}\n{recovery_methods}")
    matches = []
    for label, tokens in EQUIPMENT_RULES:
        if any(token in content for token in tokens):
            matches.append(label)
    return ordered_unique(matches, EQUIPMENT_ORDER)


def canonical_biological_material(value: str) -> list[str]:
    content = normalise_for_matching(value)
    matches = []
    for label, tokens in BIOLOGICAL_MATERIAL_RULES:
        if any(token in content for token in tokens):
            matches.append(label)
    return ordered_unique(matches, BIOLOGICAL_MATERIAL_ORDER)


def canonical_substrate_types(value: str) -> list[str]:
    items = []
    for item in split_lines(value):
        normalized = normalise_for_matching(item).rstrip(".")
        for definition in SUBSTRATE_TYPE_DEFINITIONS:
            if normalized in definition.match_terms:
                items.append(definition.label)
                break
    return ordered_unique(items, SUBSTRATE_TYPE_ORDER)


def replicate_band_key(value: str) -> str:
    if "≥" in value:
        return "high"
    if "< 10" in value:
        return "medium"
    if "≤3" in value or "not performed" in value.lower():
        return "low"
    return ""


def split_lines(value: str) -> list[str]:
    items = []
    for item in re.split(r"[\r\n]+", value):
        cleaned = re.sub(r"\s+", " ", item).strip()
        cleaned = cleaned.rstrip(" .;")
        if cleaned:
            items.append(cleaned)
    return items


def normalise_header(value: str) -> str:
    return re.sub(r"\s+", " ", clean_text(value).splitlines()[0].lower()).strip()


def normalise_for_matching(value: str) -> str:
    return re.sub(r"\s+", " ", clean_text(value).lower()).strip()


def normalise_for_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalise_for_matching(value)).strip("-")


def contains_any(value: str, tokens: Iterable[str]) -> bool:
    return any(token in value for token in tokens)


def contains_abbreviation(value: str, abbreviations: Iterable[str]) -> bool:
    return any(re.search(rf"\b{re.escape(abbreviation)}\b", value) for abbreviation in abbreviations)


def clean_text(value: str | None) -> str:
    return (value or "").replace("\xad", "")


def ordered_unique(values: Iterable[str], order: tuple[str, ...]) -> list[str]:
    unique_values = set(values)
    return [value for value in order if value in unique_values]

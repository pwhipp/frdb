from __future__ import annotations

import re
from typing import Iterable


HEADER_FIELDS = {
    "authors": "authors",
    "no. of samples (replicates)": "sample_count",
    "recovery methods": "recovery_methods",
    "equipment tested": "equipment_tested",
    "biological material": "biological_material",
    "substrate type": "substrate_type",
    "substrate descriptions": "substrate_descriptions",
    "statistical analysis": "statistical_analysis",
    "str analysis": "str_analysis",
    "results": "results",
}

REQUIRED_FIELDS = tuple(HEADER_FIELDS.values())

RECOVERY_METHOD_ORDER = (
    "Tape lift",
    "Moist swab",
    "Wet swab",
    "Wet-dry swab",
    "Swab (unspecified)",
    "Other",
)

TAPE_LIFT_TOKENS = (
    "tape-lifting",
    "tape lifting",
    "tape-lift",
    "tape lift",
)

MOIST_SWAB_TOKENS = (
    "moist",
)

WET_SWAB_TOKENS = (
    "wet-wet",
    "wet wet",
    "wet ss",
    "wet (ss)",
    "ss (wet)",
    "ss - wet",
    "wetting agents",
    "swabs with",
)

WET_SWAB_ABBREVIATIONS = (
    "ws",
)

WET_DRY_SWAB_TOKENS = (
    "wet-dry",
    "wet dry",
    "wet/dry",
    "wet and dry",
    "double swab",
    "ds technique",
    "ds method",
    "ds with",
    "wet ds",
    "dws technique",
    "dss method",
)

WET_DRY_SWAB_ABBREVIATIONS = (
    "dws",
    "dss",
)

OTHER_RECOVERY_METHOD_TOKENS = (
    "vacuum",
    "excising",
    "soaking",
    "direct lysis",
    "direct pcr",
    "fta paper-scraping",
    "scraping",
    "plasti dip",
    "untreated filter paper",
    "direct extraction",
    "cell elution",
)

EQUIPMENT_RULES = (
    ("Cotton swab", ("cotton", "150c", "cap-shure", "securswab", "dryswab")),
    ("Nylon/flocked swab", ("nylon", "floq", "flock", "purflock", "hydraflock")),
    ("Rayon swab", ("rayon", "transwab")),
    ("Foam swab", ("foam", "catch-all", "critical swab")),
    ("Polyester swab", ("polyester", "absorbond", "honeycomb", "alpha", "miraswab")),
    ("Tape lift/minitape", ("tape-lift", "tape lift", "minitape", "gellifter", "instant lifter")),
    ("Adhesive tape", ("adhesive tape", "scotch", "sellotape", "masking tape", "water-soluble", "uv-irradiated")),
    ("M-Vac/wet vacuum", ("m-vac", "wet-vacuum", "wet vacuum")),
    ("Dry vacuum", ("dry vacuum", "dna buster", "attached to a vacuum")),
    ("Pulse lavage", ("pulse lavage", "interpulse", "pulsavac")),
    ("Direct PCR/microFLOQ", ("direct pcr", "microfloq")),
    ("Filter/FTA paper", ("fta", "filter paper", "whatman")),
    ("Scraping/excision", ("scraping", "excising", "excision")),
    ("Direct lysis/extraction", ("direct lysis", "direct extraction", "autolys", "prepfiler", "ez1")),
    ("Soaking/rinse", ("soaking", "rinse", "atl buffer", "btmix")),
)

EQUIPMENT_ORDER = tuple(label for label, _ in EQUIPMENT_RULES)

BIOLOGICAL_MATERIAL_RULES = (
    ("Touch DNA", ("touch dna", "tdna", "epithelial", "eppithelial", "skin cells")),
    ("Blood", ("blood", "buffy coat")),
    ("Saliva", ("saliva",)),
    ("Buccal cells", ("buccal", "oral mucosa")),
    ("gDNA", ("gdna",)),
    ("Extracted DNA", ("extracted dna", "dna isolate")),
    ("cfDNA", ("cfdna",)),
    ("Semen", ("semen",)),
    ("Sweat", ("sweat",)),
    ("Buffy coat", ("buffy coat",)),
    ("Various", ("various",)),
)

BIOLOGICAL_MATERIAL_ORDER = tuple(label for label, _ in BIOLOGICAL_MATERIAL_RULES)
SUBSTRATE_TYPE_ORDER = ("Porous", "Non-porous", "n/a")

FILTER_HIGHLIGHT_TERMS = {
    "recovery_methods": {
        "Tape lift": ["tape-lifting", "tape lifting", "tape-lift", "tape lift"],
        "Moist swab": ["swabbing", "swab", "moist"],
        "Wet swab": ["swabbing", "swab", "wet"],
        "Wet-dry swab": ["swabbing", "swab", "wet-dry", "wet dry"],
        "Swab (unspecified)": ["swabbing", "swab"],
        "Other": [
            "vacuum",
            "excising",
            "soaking",
            "direct lysis",
            "direct pcr",
            "fta paper-scraping",
            "scraping",
            "plasti dip",
            "untreated filter paper",
            "direct extraction",
            "cell elution",
        ],
    },
    "equipment_tested": {
        "Cotton swab": ["cotton swab", "cotton", "150c"],
        "Nylon/flocked swab": ["nylon", "flocked", "floq", "flock"],
        "Rayon swab": ["rayon"],
        "Foam swab": ["foam"],
        "Polyester swab": ["polyester"],
        "Tape lift/minitape": ["tape lift", "tape-lift", "minitape", "mini-tape", "gellifter", "instant lifter"],
        "Adhesive tape": ["adhesive tape", "scotch", "sellotape", "masking tape"],
        "M-Vac/wet vacuum": ["m-vac", "wet vacuum", "wet-vacuum"],
        "Dry vacuum": ["dry vacuum", "dna buster"],
        "Pulse lavage": ["pulse lavage", "interpulse", "pulsavac"],
        "Direct PCR/microFLOQ": ["direct pcr", "microfloq"],
        "Filter/FTA paper": ["filter paper", "fta", "whatman"],
        "Scraping/excision": ["scraping", "excising", "excision"],
        "Direct lysis/extraction": ["direct lysis", "direct extraction", "autolys", "prepfiler", "ez1"],
        "Soaking/rinse": ["soaking", "rinse", "atl buffer", "btmix"],
    },
    "biological_material": {
        "Touch DNA": ["touch dna", "tdna"],
        "Blood": ["blood", "buffy coat"],
        "Saliva": ["saliva"],
        "Buccal cells": ["buccal"],
        "gDNA": ["gdna"],
        "Extracted DNA": ["extracted dna", "dna isolate"],
        "cfDNA": ["cfdna"],
        "Semen": ["semen"],
        "Sweat": ["sweat"],
        "Buffy coat": ["buffy coat"],
        "Various": ["various"],
    },
    "substrate_type": {
        "Porous": ["porous"],
        "Non-porous": ["non-porous"],
        "n/a": ["n/a"],
    },
}


def canonical_recovery_methods(recovery_methods: str, equipment: str) -> list[str]:
    recovery_content = normalise_for_matching(recovery_methods)
    content = normalise_for_matching(f"{recovery_methods}\n{equipment}")
    matches = []
    if contains_any(content, TAPE_LIFT_TOKENS):
        matches.append("Tape lift")
    if "swab" in content:
        matches.extend(canonical_swab_methods(content))
    if contains_any(recovery_content, OTHER_RECOVERY_METHOD_TOKENS):
        matches.append("Other")
    if not matches and recovery_content:
        matches.append("Other")
    return ordered_unique(matches, RECOVERY_METHOD_ORDER)


def canonical_swab_methods(content: str) -> list[str]:
    methods = []
    if contains_any(content, MOIST_SWAB_TOKENS):
        methods.append("Moist swab")
    if contains_any(content, WET_SWAB_TOKENS) or contains_abbreviation(content, WET_SWAB_ABBREVIATIONS):
        methods.append("Wet swab")
    if contains_any(content, WET_DRY_SWAB_TOKENS) or contains_abbreviation(content, WET_DRY_SWAB_ABBREVIATIONS):
        methods.append("Wet-dry swab")
    return methods or ["Swab (unspecified)"]


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
        if normalized == "porous":
            items.append("Porous")
        elif normalized == "non-porous":
            items.append("Non-porous")
        elif normalized in {"n/a", "na"}:
            items.append("n/a")
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

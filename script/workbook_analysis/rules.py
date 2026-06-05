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

RECOVERY_METHOD_RULES = (
    ("swabbing", "Swabbing"),
    ("tape-lifting", "Tape-lifting"),
    ("tape lifting", "Tape-lifting"),
    ("vacuum", "Vacuum"),
    ("excising", "Excising"),
    ("soaking", "Soaking"),
    ("direct lysis", "Direct lysis"),
    ("direct pcr", "Direct PCR"),
    ("fta paper-scraping", "FTA paper-scraping"),
    ("scraping", "Scraping"),
    ("plasti dip", "Plasti dip"),
    ("untreated filter paper", "Untreated filter paper"),
    ("direct extraction", "Direct extraction"),
    ("cell elution", "Cell elution"),
)

RECOVERY_METHOD_ORDER = (
    "Swabbing",
    "Tape-lifting",
    "Vacuum",
    "Excising",
    "Soaking",
    "Direct lysis",
    "Direct PCR",
    "FTA paper-scraping",
    "Scraping",
    "Plasti dip",
    "Untreated filter paper",
    "Direct extraction",
    "Cell elution",
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
        "Swabbing": ["swabbing", "swab"],
        "Tape-lifting": ["tape-lifting", "tape lifting", "tape-lift", "tape lift"],
        "Vacuum": ["vacuum", "m-vac"],
        "Excising": ["excising", "excise"],
        "Soaking": ["soaking", "soak"],
        "Direct lysis": ["direct lysis"],
        "Direct PCR": ["direct pcr"],
        "FTA paper-scraping": ["fta paper-scraping", "fta", "paper-scraping"],
        "Scraping": ["scraping", "scrape"],
        "Plasti dip": ["plasti dip"],
        "Untreated filter paper": ["untreated filter paper", "filter paper"],
        "Direct extraction": ["direct extraction"],
        "Cell elution": ["cell elution"],
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


def canonical_recovery_methods(value: str) -> list[str]:
    normalized_items = [normalise_for_matching(item) for item in split_lines(value)]
    matches = []
    for token, label in RECOVERY_METHOD_RULES:
        if any(token in item for item in normalized_items):
            matches.append(label)
    return ordered_unique(matches, RECOVERY_METHOD_ORDER)


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


def clean_text(value: str | None) -> str:
    return (value or "").replace("\xad", "")


def ordered_unique(values: Iterable[str], order: tuple[str, ...]) -> list[str]:
    unique_values = set(values)
    return [value for value in order if value in unique_values]

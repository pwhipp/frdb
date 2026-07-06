from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleDefinition:
    """Canonical label and source text terms for one workbook classification."""

    label: str
    match_terms: tuple[str, ...]
    whole_word_terms: tuple[str, ...] = ()
    highlight_terms: tuple[str, ...] = ()


# Source workbook column headings mapped to FRDB's internal field names.
# Update this only when the incoming spreadsheet uses a new accepted heading.
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


# Recovery method labels and normalized text terms. Labels are the canonical
# display values; match terms are lower-case text fragments searched in workbook
# cells. Highlight terms are only supplied where UI highlighting should differ
# from matching.
RECOVERY_METHOD_DEFINITIONS = (
    RuleDefinition(
        label="Tape lift",
        match_terms=("tape-lifting", "tape lifting", "tape-lift", "tape lift"),
    ),
    RuleDefinition(
        label="Moist swab",
        match_terms=("moist",),
        highlight_terms=("swabbing", "swab", "moist"),
    ),
    RuleDefinition(
        label="Wet swab",
        match_terms=(
            "wet-wet",
            "wet wet",
            "wet ss",
            "wet (ss)",
            "ss (wet)",
            "ss - wet",
            "wetting agents",
            "swabs with",
        ),
        whole_word_terms=("ws",),
        highlight_terms=("swabbing", "swab", "wet"),
    ),
    RuleDefinition(
        label="Wet-dry swab",
        match_terms=(
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
        ),
        whole_word_terms=("dws", "dss"),
        highlight_terms=("swabbing", "swab", "wet-dry", "wet dry"),
    ),
    RuleDefinition(
        label="Swab (unspecified)",
        match_terms=(),
        highlight_terms=("swabbing", "swab"),
    ),
    RuleDefinition(
        label="Other",
        match_terms=(
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
        ),
    ),
)

# If any trigger term is present and no specific swab subtype matches, the
# recovery method is classified as "Swab (unspecified)".
SWAB_RECOVERY_TRIGGER_TERMS = ("swab",)
SWAB_METHOD_LABELS = ("Moist swab", "Wet swab", "Wet-dry swab")
SWAB_UNSPECIFIED_LABEL = "Swab (unspecified)"


# Equipment labels and normalized text terms. Labels are canonical filter
# values; match terms include brand, material, and technique wording observed in
# source studies.
EQUIPMENT_DEFINITIONS = (
    RuleDefinition(
        label="Cotton swab",
        match_terms=("cotton", "150c", "cap-shure", "securswab", "dryswab"),
        highlight_terms=("cotton swab", "cotton", "150c"),
    ),
    RuleDefinition(
        label="Nylon/flocked swab",
        match_terms=("nylon", "floq", "flock", "purflock", "hydraflock"),
        highlight_terms=("nylon", "flocked", "floq", "flock"),
    ),
    RuleDefinition(
        label="Rayon swab",
        match_terms=("rayon", "transwab"),
        highlight_terms=("rayon",),
    ),
    RuleDefinition(
        label="Foam swab",
        match_terms=("foam", "catch-all", "critical swab"),
        highlight_terms=("foam",),
    ),
    RuleDefinition(
        label="Polyester swab",
        match_terms=("polyester", "absorbond", "honeycomb", "alpha", "miraswab"),
        highlight_terms=("polyester",),
    ),
    RuleDefinition(
        label="Tape lift/minitape",
        match_terms=(
            "tape-lift",
            "tape lift",
            "minitape",
            "gellifter",
            "instant lifter",
        ),
        highlight_terms=(
            "tape lift",
            "tape-lift",
            "minitape",
            "mini-tape",
            "gellifter",
            "instant lifter",
        ),
    ),
    RuleDefinition(
        label="Adhesive tape",
        match_terms=(
            "adhesive tape",
            "scotch",
            "sellotape",
            "masking tape",
            "water-soluble",
            "uv-irradiated",
        ),
        highlight_terms=("adhesive tape", "scotch", "sellotape", "masking tape"),
    ),
    RuleDefinition(
        label="M-Vac/wet vacuum",
        match_terms=("m-vac", "wet-vacuum", "wet vacuum"),
        highlight_terms=("m-vac", "wet vacuum", "wet-vacuum"),
    ),
    RuleDefinition(
        label="Dry vacuum",
        match_terms=("dry vacuum", "dna buster", "attached to a vacuum"),
        highlight_terms=("dry vacuum", "dna buster"),
    ),
    RuleDefinition(
        label="Pulse lavage",
        match_terms=("pulse lavage", "interpulse", "pulsavac"),
    ),
    RuleDefinition(
        label="Direct PCR/microFLOQ",
        match_terms=("direct pcr", "microfloq"),
    ),
    RuleDefinition(
        label="Filter/FTA paper",
        match_terms=("fta", "filter paper", "whatman"),
        highlight_terms=("filter paper", "fta", "whatman"),
    ),
    RuleDefinition(
        label="Scraping/excision",
        match_terms=("scraping", "excising", "excision"),
    ),
    RuleDefinition(
        label="Direct lysis/extraction",
        match_terms=("direct lysis", "direct extraction", "autolys", "prepfiler", "ez1"),
    ),
    RuleDefinition(
        label="Soaking/rinse",
        match_terms=("soaking", "rinse", "atl buffer", "btmix"),
    ),
)


# Biological material labels and normalized text terms. Labels are the
# canonical biological material categories reviewed for the app; match terms
# are lower-case source wording variants that should map to each category.
BIOLOGICAL_MATERIAL_DEFINITIONS = (
    RuleDefinition(
        label="Touch DNA",
        match_terms=("touch dna", "tdna", "epithelial", "eppithelial", "skin cells"),
        highlight_terms=("touch dna", "tdna"),
    ),
    RuleDefinition(label="Blood", match_terms=("blood", "buffy coat")),
    RuleDefinition(label="Saliva", match_terms=("saliva",)),
    RuleDefinition(
        label="Buccal cells",
        match_terms=("buccal", "oral mucosa"),
        highlight_terms=("buccal",),
    ),
    RuleDefinition(label="gDNA", match_terms=("gdna",)),
    RuleDefinition(label="Extracted DNA", match_terms=("extracted dna", "dna isolate")),
    RuleDefinition(label="cfDNA", match_terms=("cfdna",)),
    RuleDefinition(label="Semen", match_terms=("semen",)),
    RuleDefinition(label="Sweat", match_terms=("sweat",)),
    RuleDefinition(label="Buffy coat", match_terms=("buffy coat",)),
    RuleDefinition(label="Various", match_terms=("various",)),
)


# Substrate type labels and exact normalized source values. These are matched
# after each source cell is split into separate lines.
SUBSTRATE_TYPE_DEFINITIONS = (
    RuleDefinition(label="Porous", match_terms=("porous",)),
    RuleDefinition(label="Non-porous", match_terms=("non-porous",)),
    RuleDefinition(label="n/a", match_terms=("n/a", "na"), highlight_terms=("n/a",)),
)


# Filterable fields in the generated app, linked to the definitions that drive
# the highlight term JSON.
FILTER_DEFINITIONS = {
    "recovery_methods": RECOVERY_METHOD_DEFINITIONS,
    "equipment_tested": EQUIPMENT_DEFINITIONS,
    "biological_material": BIOLOGICAL_MATERIAL_DEFINITIONS,
    "substrate_type": SUBSTRATE_TYPE_DEFINITIONS,
}

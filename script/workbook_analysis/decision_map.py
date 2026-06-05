from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from .rules import BIOLOGICAL_MATERIAL_ORDER, canonical_biological_material


TARGET_METHODS = [
    "tape lift",
    "moist swab",
    "wet swab",
    "wet-dry swab",
    "swab - unspecified moisture",
]
DECISION_METHODS = ["tape lift", "moist swab", "wet swab", "wet-dry swab"]
BIO_ORDER = [item for item in BIOLOGICAL_MATERIAL_ORDER if item != "Various"]
SURFACE_ORDER = ["Porous", "Non-porous"]
METHOD_FILTER_VALUES = {
    "tape lift": "Tape lift",
    "moist swab": "Moist swab",
    "wet swab": "Wet swab",
    "wet-dry swab": "Wet-dry swab",
    "swab - unspecified moisture": "Swab (unspecified)",
}

METHOD_NORMALIZATION = [
    {
        "normalized_method": "tape lift",
        "mapping_rule": "Tape lift, tape lifting, TL, minitape, gel/instant/gelatine lifter, masking/packing tape when used as lift",
        "aggregation_note": "Direct target technique.",
    },
    {
        "normalized_method": "moist swab",
        "mapping_rule": "Moist swab, wet-moist, both-moist double swab",
        "aggregation_note": "Kept separate from wet swab and wet-dry swab.",
    },
    {
        "normalized_method": "wet swab",
        "mapping_rule": "Wet swab, single wet swab, wet single swab, WS technique, pre-moistened/moistened collection, swab plus wetting agent",
        "aggregation_note": "Interprets web swab/web swap as wet swab.",
    },
    {
        "normalized_method": "wet-dry swab",
        "mapping_rule": "Wet-dry, moist-dry, dry swab following a wet/moist swab, DSS where source summary identifies wet-dry",
        "aggregation_note": "Double swab is not automatically mapped here unless wet/moist plus dry is stated.",
    },
    {
        "normalized_method": "swab - unspecified moisture",
        "mapping_rule": "Swab, cotton/rayon/foam/polyester/nylon/FLOQ/PurFlock/SafeDry etc. where wetting state is not explicit",
        "aggregation_note": "Kept as a separate evidence bucket to avoid overclaiming wet/moist/wet-dry specificity.",
    },
]

SCORING_README = [
    {"rule": "Clear statistically significant win/loss", "score_effect": "+2 / -2"},
    {"rule": "Mixed significance within a row", "score_effect": "+1 / -1"},
    {"rule": "Directional result with p-value not stated or unclear", "score_effect": "+0.5 / -0.5"},
    {"rule": "Directional result with no statistical test or not significant", "score_effect": "+0.25 / -0.25"},
    {"rule": "Equivalent/no clear better method", "score_effect": "Tie count only; no score movement"},
    {
        "rule": "Confidence",
        "score_effect": "High/moderate/low based on unique study count, top-method margin, and significant contradictions. This is an evidence-map confidence, not a meta-analysis.",
    },
]

README_ITEMS = [
    {
        "item": "Purpose",
        "description": "Decision map: biological material versus porous/non-porous surface, with ranked recovery techniques and study counts.",
    },
    {
        "item": "Detailed evidence",
        "description": "Technique rankings contain scores, wins/losses/ties, significant wins/losses, supporting authors, and source-row trace notes. Scored comparisons show how each extracted comparison was normalized.",
    },
    {
        "item": "Important caveat",
        "description": "Many studies report swabbing without enough detail to classify moisture state. Those rows are kept as swab - unspecified moisture and shown separately from requested wet/moist/wet-dry classes.",
    },
]


def build_decision_map(comparison_rows: list[dict[str, str]], publication_rows: list[dict]) -> dict:
    publication_id_by_author = {row["authors"]: row["id"] for row in publication_rows}
    metrics, scored_rows = score_comparisons(comparison_rows, publication_id_by_author)
    cells = build_decision_cells(metrics)
    rankings = build_technique_rankings(metrics)
    return {
        "bio_order": BIO_ORDER,
        "surface_order": SURFACE_ORDER,
        "cells": cells,
        "matrix": matrix_from_cells(cells),
        "technique_rankings": rankings,
        "scored_comparisons": scored_rows,
        "method_normalization": METHOD_NORMALIZATION,
        "scoring_readme": SCORING_README,
        "readme": README_ITEMS,
    }


def score_comparisons(
    rows: list[dict[str, str]],
    publication_id_by_author: dict[str, int],
) -> tuple[dict, list[dict]]:
    metrics = defaultdict(lambda: defaultdict(empty_metric))
    scored_rows = []

    for row in rows:
        bio_values = biological_materials(row)
        if not bio_values:
            continue
        surface_values = surfaces(row.get("substrate_class", ""))
        if not surface_values:
            continue

        better_methods = extract_methods(row.get("better_method_class", ""), row.get("better_recovery_method", ""))
        worse_methods = extract_methods(row.get("worse_method_class", ""), row.get("worse_recovery_method", ""))
        worse_methods -= better_methods
        tie_methods = set()
        equivalent = is_equivalent_row(row)
        if equivalent:
            tie_methods = extract_methods(
                row.get("comparison_scope", ""),
                row.get("notes_source_result_summary", ""),
                row.get("better_recovery_method", ""),
                row.get("worse_recovery_method", ""),
            ) | better_methods | worse_methods

        weight, significant, weight_note = evidence_weight(row.get("statistical_significance", ""))
        publication_id = publication_id_by_author[row["author"]]
        for bio in bio_values:
            for surface in surface_values:
                cell_key = (bio, surface)
                if equivalent and len(tie_methods) >= 2:
                    for method in tie_methods & set(TARGET_METHODS):
                        add_metric(metrics[cell_key], method, row, publication_id, tie=True, note=f"{row['source_excel_row']}: tie/equivalent evidence")
                    contribution = "tie"
                else:
                    for method in better_methods & set(TARGET_METHODS):
                        add_metric(metrics[cell_key], method, row, publication_id, delta=weight, win=True, significant=significant, note=f"{row['source_excel_row']}: {weight_note}")
                    for method in worse_methods & set(TARGET_METHODS):
                        add_metric(metrics[cell_key], method, row, publication_id, delta=-weight, loss=True, significant=significant, note=f"{row['source_excel_row']}: {weight_note}")
                    contribution = "directional"
                scored_rows.append(scored_comparison_row(row, bio, surface, better_methods, worse_methods, tie_methods, weight, contribution, publication_id))

    return metrics, scored_rows


def biological_materials(row: dict[str, str]) -> list[str]:
    biological_class = row.get("biological_material_class", "")
    if biological_class in BIO_ORDER:
        return [biological_class]
    return [item for item in canonical_biological_material(row.get("biological_material_detail", "")) if item in BIO_ORDER]


def empty_metric() -> dict:
    return {
        "score": 0.0,
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "significant_wins": 0,
        "significant_losses": 0,
        "comparisons": 0,
        "studies": set(),
        "publication_ids": set(),
        "authors": set(),
        "notes": [],
    }


def add_metric(metrics: dict, method: str, row: dict[str, str], publication_id: int, delta: float = 0.0, win: bool = False, loss: bool = False, tie: bool = False, significant: bool = False, note: str = "") -> None:
    metric = metrics[method]
    metric["score"] += delta
    metric["wins"] += int(win)
    metric["losses"] += int(loss)
    metric["ties"] += int(tie)
    metric["significant_wins"] += int(win and significant)
    metric["significant_losses"] += int(loss and significant)
    metric["comparisons"] += 1
    metric["studies"].add(row["source_excel_row"])
    metric["publication_ids"].add(publication_id)
    metric["authors"].add(row["author"])
    if note:
        metric["notes"].append(note)


def build_decision_cells(metrics: dict) -> list[dict]:
    cells = []
    for bio in BIO_ORDER:
        for surface in SURFACE_ORDER:
            cell_metrics = metrics[(bio, surface)]
            requested_publication_ids = sorted(set().union(*(cell_metrics[method]["publication_ids"] for method in DECISION_METHODS)))
            all_publication_ids = sorted(set().union(*(cell_metrics[method]["publication_ids"] for method in TARGET_METHODS)))
            confidence, rationale = confidence_for(cell_metrics, DECISION_METHODS)
            rankings = ranked_methods(cell_metrics, DECISION_METHODS, bio, surface)
            cells.append({
                "biological_material": bio,
                "surface": surface,
                "confidence": confidence,
                "confidence_rationale": rationale,
                "unique_studies_requested_methods": len(requested_publication_ids),
                "unique_studies_including_unspecified_swab": len(all_publication_ids),
                "publication_ids": requested_publication_ids,
                "all_publication_ids": all_publication_ids,
                "rankings": rankings,
                "ranking_with_unspecified_swab_bucket": ranked_methods(cell_metrics, TARGET_METHODS, bio, surface),
                "top_requested_method": top_method_text(rankings),
            })
    return cells


def build_technique_rankings(metrics: dict) -> list[dict]:
    rows = []
    for bio in BIO_ORDER:
        for surface in SURFACE_ORDER:
            for item in ranked_methods(metrics[(bio, surface)], TARGET_METHODS, bio, surface):
                rows.append({
                    "biological_material": bio,
                    "surface": surface,
                    "method": item["method"],
                    "score": f"{item['score']:.2f}",
                    "unique_studies": item["unique_studies"],
                    "comparison_contributions": item["comparison_contributions"],
                    "wins": item["wins"],
                    "losses": item["losses"],
                    "ties": item["ties"],
                    "significant_wins": item["significant_wins"],
                    "significant_losses": item["significant_losses"],
                    "supporting_authors": "; ".join(item["authors"]),
                    "trace_notes": "; ".join(item["notes"][:20]),
                    "publication_ids": item["publication_ids"],
                })
    return rows


def ranked_methods(cell_metrics: dict[str, dict], allowed_methods: Iterable[str], bio: str, surface: str) -> list[dict]:
    ranked = [(method, cell_metrics[method]) for method in allowed_methods if cell_metrics[method]["comparisons"] > 0]
    ranked.sort(key=lambda item: (item[1]["score"], item[1]["significant_wins"], len(item[1]["studies"]), -item[1]["significant_losses"]), reverse=True)
    return [ranking_item(index, method, data, bio, surface) for index, (method, data) in enumerate(ranked, start=1)]


def ranking_item(index: int, method: str, data: dict, bio: str, surface: str) -> dict:
    return {
        "rank": index,
        "method": method,
        "method_filter_value": METHOD_FILTER_VALUES[method],
        "score_key": score_key(bio, surface, method),
        "win_key": contribution_key(bio, surface, method, "win"),
        "loss_key": contribution_key(bio, surface, method, "loss"),
        "tie_key": contribution_key(bio, surface, method, "tie"),
        "score": data["score"],
        "unique_studies": len(data["publication_ids"]),
        "comparison_contributions": data["comparisons"],
        "wins": data["wins"],
        "losses": data["losses"],
        "ties": data["ties"],
        "significant_wins": data["significant_wins"],
        "significant_losses": data["significant_losses"],
        "publication_ids": sorted(data["publication_ids"]),
        "authors": sorted(data["authors"]),
        "notes": data["notes"],
    }


def matrix_from_cells(cells: list[dict]) -> list[dict]:
    by_key = {(cell["biological_material"], cell["surface"]): cell for cell in cells}
    return [{"biological_material": bio, "surfaces": [by_key[(bio, surface)] for surface in SURFACE_ORDER]} for bio in BIO_ORDER]


def top_method_text(rankings: list[dict]) -> str:
    if not rankings:
        return "No direct requested-method leader"
    top = rankings[0]
    return f"{top['rank']}. {top['method']} (score {top['score']:+.2f}; studies {top['unique_studies']}; wins/losses/ties {top['wins']}/{top['losses']}/{top['ties']}; sig wins/losses {top['significant_wins']}/{top['significant_losses']})"


def scored_comparison_row(row: dict[str, str], bio: str, surface: str, better_methods: set[str], worse_methods: set[str], tie_methods: set[str], weight: float, contribution: str, publication_id: int) -> dict:
    score_contributions = score_contributions_for_row(bio, surface, better_methods, worse_methods, tie_methods, weight, contribution)
    return {
        **row,
        "publication_id": publication_id,
        "decision_bio": bio,
        "decision_surface": surface,
        "normalized_better_methods": "; ".join(sorted(better_methods)) or "none",
        "normalized_worse_methods": "; ".join(sorted(worse_methods)) or "none",
        "normalized_tie_methods": "; ".join(sorted(tie_methods)) or "none",
        "score_contributions": score_contributions,
        "contribution_keys": contribution_keys(score_contributions),
        "score_contribution_summary": score_contribution_summary(score_contributions),
        "score_contribution_type": contribution,
    }


def score_contributions_for_row(bio: str, surface: str, better_methods: set[str], worse_methods: set[str], tie_methods: set[str], weight: float, contribution: str) -> dict[str, float]:
    if contribution == "tie":
        return {
            score_key(bio, surface, method): 0.0
            for method in sorted(tie_methods & set(TARGET_METHODS))
        }

    contributions = {}
    for method in sorted(better_methods & set(TARGET_METHODS)):
        contributions[score_key(bio, surface, method)] = weight
    for method in sorted(worse_methods & set(TARGET_METHODS)):
        contributions[score_key(bio, surface, method)] = -weight
    return contributions


def score_contribution_summary(contributions: dict[str, float]) -> str:
    parts = []
    for key, value in contributions.items():
        method = key.rsplit("|", 1)[-1]
        parts.append(f"{method} {value:+.2f}")
    return "; ".join(parts)


def contribution_keys(contributions: dict[str, float]) -> list[str]:
    return [f"{key}|{'win' if value > 0 else 'loss' if value < 0 else 'tie'}" for key, value in contributions.items()]


def score_key(bio: str, surface: str, method: str) -> str:
    return f"{bio}|{surface}|{method}"


def contribution_key(bio: str, surface: str, method: str, kind: str) -> str:
    return f"{score_key(bio, surface, method)}|{kind}"


def surfaces(substrate_class: str) -> list[str]:
    text = substrate_class.lower()
    if "porous and non-porous" in text or ("porous" in text and "non-porous" in text):
        return ["Porous", "Non-porous"]
    if "non-porous" in text:
        return ["Non-porous"]
    if "porous" in text:
        return ["Porous"]
    return []


def extract_methods(*parts: str, include_generic_swab: bool = True) -> set[str]:
    text = normalize_text(*parts)
    methods = set()
    if re.search(r"\b(tape\s*-?\s*lift|tape\s*lifting|minitape|mini-tape|\btl\b|gellifter|instant lifter|gelatine lifter|masking tape|packing tape|scenesafe fast|scotch magic|solder tape)", text):
        methods.add("tape lift")
    if re.search(r"(wet-dry|moist-dry|wet\s*dry|dss method|dry swab follows|followed by a dry swab)", text):
        methods.add("wet-dry swab")
    if re.search(r"(wet-moist|moist swab|moist double|moist ds|both moist)", text):
        methods.add("moist swab")
    if re.search(r"(single wet|wet single|wet swab|wet\s*\(|\bws technique\b|pre-moistened|moistened skin|wetting agent|pbs wetting|water before collection)", text):
        methods.add("wet swab")
    if include_generic_swab and re.search(r"\b(swab|swabbing|flock|floq|cotton|rayon|foam|polyester|nylon|safedry|purflock|x-swab|ishelix|isohelix|hydraflock|miraswab|critical swab|microfloq)\b", text):
        if not ({"wet swab", "moist swab", "wet-dry swab"} & methods):
            methods.add("swab - unspecified moisture")
    return methods


def normalize_text(*parts: str) -> str:
    text = " ".join(parts).lower().replace("\u00ad", "")
    return text.replace("wet dry", "wet-dry").replace("wet/dry", "wet-dry").replace("moist dry", "moist-dry").replace("moist/dry", "moist-dry").replace("double-swab", "double swab").replace("double-swabbing", "double swabbing")


def is_equivalent_row(row: dict[str, str]) -> bool:
    text = normalize_text(row.get("better_recovery_method", ""), row.get("better_method_class", ""), row.get("worse_recovery_method", ""), row.get("worse_method_class", ""), row.get("statistical_significance", ""))
    return any(token in text for token in ["no clear better", "no clear worse", "equivalent", "comparable", "no difference", "not significant / equal", "mostly not significant"]) and "directionally" not in text


def evidence_weight(sig_text: str) -> tuple[float, bool, str]:
    text = normalize_text(sig_text)
    if "not performed" in text:
        return 0.25, False, "directional/no statistical test"
    if "not significant" in text or "no statistical difference" in text or "no difference" in text or "comparable" in text or "equivalent" in text:
        return 0.25, False, "directional but not statistically significant/equivalent context"
    if "mixed" in text and "significant" in text:
        return 1.0, True, "mixed significance"
    if "significant" in text or re.search(r"p\s*[<=>]", text):
        return 2.0, True, "statistically significant"
    if "p-value not stated" in text or "not stated" in text or "pairwise" in text:
        return 0.5, False, "directional; p-value not stated in source summary"
    return 0.5, False, "directional; significance unclear"


def confidence_for(cell_metrics: dict[str, dict], allowed_methods: list[str]) -> tuple[str, str]:
    ranked = [(method, cell_metrics[method]) for method in allowed_methods if cell_metrics[method]["comparisons"] > 0]
    ranked.sort(key=lambda item: (item[1]["score"], item[1]["significant_wins"], len(item[1]["studies"]), -item[1]["significant_losses"]), reverse=True)
    if not ranked:
        return "No direct evidence", "No requested-method evidence after normalization."
    total_studies = len(set().union(*(data["studies"] for _, data in ranked)))
    top_method, top = ranked[0]
    second_score = ranked[1][1]["score"] if len(ranked) > 1 else 0.0
    margin = top["score"] - second_score
    if top["score"] <= 0 or margin < 0.5:
        return "Low", f"Mixed or tied evidence; top method {top_method} has little separation."
    if total_studies >= 5 and len(top["studies"]) >= 3 and margin >= 2 and top["significant_losses"] == 0:
        return "High", f"{total_studies} studies in cell; {top_method} is separated from alternatives and has no significant losses."
    if total_studies >= 3 and len(top["studies"]) >= 2 and margin >= 1:
        return "Moderate", f"{total_studies} studies in cell; {top_method} leads but evidence is not uniformly strong."
    return "Low", f"Limited evidence; {total_studies} {'study' if total_studies == 1 else 'studies'} in cell or small score margin."

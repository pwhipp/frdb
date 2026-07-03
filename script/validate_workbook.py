#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workbook_analysis.comparisons import parse_comparisons
from workbook_analysis.read_excel import read_excel


def main() -> None:
    arguments = parse_args()
    workbook_path = arguments.workbook.resolve()
    comparisons_path = (arguments.comparisons_workbook or workbook_path).resolve()
    publication_rows = read_excel(workbook_path)
    comparison_rows = parse_comparisons(
        comparisons_path,
        publication_rows,
        arguments.comparisons_sheet,
        require_all_studies=not arguments.allow_missing_comparisons,
    )
    print(f"Validated {len(publication_rows)} studies and {len(comparison_rows)} comparison rows")
    print(f"Comparison sheet: {comparisons_path} [{arguments.comparisons_sheet}]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an FRDB source workbook without writing generated data.")
    parser.add_argument("workbook", type=Path, help="Path to the source .xlsx workbook.")
    parser.add_argument(
        "--comparisons-workbook",
        type=Path,
        help="Path to a workbook containing the comparison sheet. Defaults to the source workbook.",
    )
    parser.add_argument(
        "--comparisons-sheet",
        default="Comparisons",
        help="Name of the comparison worksheet to validate. Defaults to Comparisons.",
    )
    parser.add_argument(
        "--allow-missing-comparisons",
        action="store_true",
        help="Allow studies with no comparison rows. Use only for partial AI draft sheets.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"validate_workbook.py: {error}", file=sys.stderr)
        raise SystemExit(1) from error

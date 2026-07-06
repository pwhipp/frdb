#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workbook_analysis.source_workbook import (
    CANONICAL_WORKBOOK_RELATIVE_PATH,
    DEFAULT_COMPARISONS_SHEET,
    inspect_combined_workbook,
    resolve_workbook_path,
)
from workbook_analysis.workbook import parse_workbook


def main() -> None:
    arguments = parse_args()
    workbook_path = resolve_workbook_path(REPO_ROOT, arguments.workbook)
    workbook = inspect_combined_workbook(workbook_path, arguments.comparisons_sheet)
    parsed_workbook = parse_workbook(
        workbook.path,
        arguments.comparisons_sheet,
        require_all_studies=not arguments.allow_missing_comparisons,
    )
    print(f"Validated {len(parsed_workbook.rows)} studies and {len(parsed_workbook.comparisons)} comparison rows")
    print(f"Workbook: {workbook.path}")
    print(f"Studies sheet: {workbook.study_sheet}")
    print(f"Comparison sheet: {workbook.comparisons_sheet}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an FRDB source workbook without writing generated data.")
    parser.add_argument(
        "workbook",
        nargs="?",
        type=Path,
        help=f"Path to the combined source .xlsx workbook. Defaults to {CANONICAL_WORKBOOK_RELATIVE_PATH}.",
    )
    parser.add_argument(
        "--comparisons-sheet",
        default=DEFAULT_COMPARISONS_SHEET,
        help=f"Name of the comparison worksheet in the combined workbook. Defaults to {DEFAULT_COMPARISONS_SHEET}.",
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

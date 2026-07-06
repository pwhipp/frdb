#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workbook_analysis.output import assign_publication_ids, default_output_folder, write_data_files
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
    output_folder = (arguments.output_folder or default_output_folder(REPO_ROOT)).resolve()
    parsed_workbook = parse_workbook(workbook.path, workbook.comparisons_sheet)
    rows = assign_publication_ids(output_folder, workbook_path, parsed_workbook.rows)
    write_data_files(output_folder, rows, parsed_workbook.publication_filters, parsed_workbook.comparisons, arguments.compact)
    print(f"Wrote {len(rows)} publications to {output_folder}")
    print(f"Workbook: {workbook.path}")
    print(f"Studies sheet: {workbook.study_sheet}")
    print(f"Comparison sheet: {workbook.comparisons_sheet}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate FRDB data from an Excel workbook.")
    parser.add_argument(
        "workbook",
        nargs="?",
        type=Path,
        help=f"Path to the combined source .xlsx workbook. Defaults to {CANONICAL_WORKBOOK_RELATIVE_PATH}.",
    )
    parser.add_argument(
        "--output-folder",
        type=Path,
        help="Folder for generated JSON data. Defaults to data/.",
    )
    parser.add_argument(
        "--comparisons-sheet",
        default=DEFAULT_COMPARISONS_SHEET,
        help=f"Name of the comparison worksheet in the combined workbook. Defaults to {DEFAULT_COMPARISONS_SHEET}.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON instead of the default indented JSON.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"analyze_workbook.py: {error}", file=sys.stderr)
        raise SystemExit(1) from error

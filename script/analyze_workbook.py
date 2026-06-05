from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workbook_analysis.excel import parse_workbook
from workbook_analysis.output import default_output_folder, merge_existing_rows, write_analysis_json


def main() -> None:
    arguments = parse_args()
    workbook_path = arguments.workbook.resolve()
    output_folder = (arguments.output_folder or default_output_folder(REPO_ROOT)).resolve()
    generated_rows = parse_workbook(workbook_path)
    rows = merge_existing_rows(output_folder, workbook_path, generated_rows)
    write_analysis_json(output_folder, rows, arguments.compact)
    print(f"Wrote {len(rows)} publications to {output_folder}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate FRDB data from an Excel workbook.")
    parser.add_argument("workbook", type=Path, help="Path to the source .xlsx workbook.")
    parser.add_argument(
        "--output-folder",
        type=Path,
        help="Folder for generated JSON data. Defaults to data/.",
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

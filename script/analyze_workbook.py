from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workbook_analysis.output import assign_publication_ids, default_output_folder, write_data_files
from workbook_analysis.workbook import parse_workbook


def main() -> None:
    arguments = parse_args()
    workbook_path = arguments.workbook.resolve()
    output_folder = (arguments.output_folder or default_output_folder(REPO_ROOT)).resolve()
    parsed_workbook = parse_workbook(workbook_path)
    rows = assign_publication_ids(output_folder, workbook_path, parsed_workbook.rows)
    write_data_files(output_folder, rows, parsed_workbook.publication_filters, arguments.compact)
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

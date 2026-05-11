from __future__ import annotations

import argparse
from pathlib import Path
import sys

from workbook_analysis.excel import parse_workbook
from workbook_analysis.output import default_output_path, merge_existing_rows, write_data_module


REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    arguments = parse_args()
    workbook_path = arguments.workbook.resolve()
    output_path = arguments.output or default_output_path(REPO_ROOT, workbook_path)
    generated_rows = parse_workbook(workbook_path)
    rows = merge_existing_rows(output_path, generated_rows)
    write_data_module(output_path, workbook_path, rows)
    print(f"Wrote {len(rows)} rows to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate FRDB data from an Excel workbook.")
    parser.add_argument("workbook", type=Path, help="Path to the source .xlsx workbook.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Generated Python data module. Defaults to data/<workbook-stem>.py.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"analyze_workbook.py: {error}", file=sys.stderr)
        raise SystemExit(1) from error

"""CLI entry point for producing a standardized cleaned transactional CSV."""

from __future__ import annotations

import argparse

from app.api.cleaning_service import run_cleaning_pipeline


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the cleaning job."""
    parser = argparse.ArgumentParser(description="Normalize a transactional CSV into a standardized backend dataset.")
    parser.add_argument("csv_path", help="Input transactional CSV path")
    parser.add_argument(
        "--output",
        dest="output_path",
        default="sample_cleaned_standardized.csv",
        help="Output CSV path for the standardized dataset",
    )
    return parser


def main() -> None:
    """Run the cleaning pipeline and print a compact summary."""
    args = build_parser().parse_args()
    result = run_cleaning_pipeline(csv_path=args.csv_path, output_path=args.output_path)
    print(f"Rows processed: {result['rows_processed']}")
    print(f"Output written to: {args.output_path}")


if __name__ == "__main__":
    main()

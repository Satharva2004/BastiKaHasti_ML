"""Command-line entry point for Phase 1 fraud feature engineering."""

from __future__ import annotations

import argparse

from app.api.service import run_feature_pipeline


def build_parser() -> argparse.ArgumentParser:
    """Create a simple CLI for batch feature-engineering jobs."""
    parser = argparse.ArgumentParser(description="Run Phase 1 fraud feature engineering on a CSV file.")
    parser.add_argument("csv_path", help="Input transactional CSV path")
    parser.add_argument(
        "--output",
        dest="output_path",
        default="engineered_fraud_features.csv",
        help="Optional output CSV path for engineered features",
    )
    return parser


def main() -> None:
    """Run the pipeline and print a compact backend job summary."""
    args = build_parser().parse_args()
    result = run_feature_pipeline(csv_path=args.csv_path, output_path=args.output_path)
    print(f"Rows processed: {result['rows_processed']}")
    print(f"Output written to: {args.output_path}")


if __name__ == "__main__":
    main()

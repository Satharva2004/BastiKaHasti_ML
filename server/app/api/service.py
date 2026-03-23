"""Thin backend service layer for the fraud feature pipeline."""

from __future__ import annotations

from typing import Optional

from app.core.pipeline import FraudFeatureEngineer
from app.schemas.response import PipelineResult


def run_feature_pipeline(csv_path: str, output_path: Optional[str] = None) -> PipelineResult:
    """Execute the feature-engineering job and optionally persist the result."""
    dataframe, summary = FraudFeatureEngineer(csv_path=csv_path).run()

    if output_path:
        dataframe.to_csv(output_path, index=False)

    return {
        "rows_processed": int(len(dataframe)),
        "columns_produced": list(dataframe.columns),
        "summary": summary,
        "dataframe": dataframe,
    }

"""Service response schema definitions."""

from __future__ import annotations

from typing import Dict, List, TypedDict

import pandas as pd


class FraudLabelCounts(TypedDict):
    """Summary counts for final fraud labels."""

    non_fraud: int
    fraud: int


class PipelineSummary(TypedDict):
    """Top-level fraud pattern summary."""

    fraud_label_counts: FraudLabelCounts
    pattern_counts: Dict[str, int]


class PipelineResult(TypedDict):
    """Backend response payload for a completed feature-engineering job."""

    rows_processed: int
    columns_produced: List[str]
    summary: PipelineSummary
    dataframe: pd.DataFrame

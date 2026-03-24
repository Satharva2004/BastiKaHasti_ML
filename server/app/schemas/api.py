"""Pydantic API response schemas for the cleaning endpoints."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class QualityMetrics(BaseModel):
    """High-signal cleaning quality counts for frontend display."""

    unknown_device_count: int
    unknown_payment_method_count: int
    unknown_merchant_category_count: int
    invalid_ip_count: int
    zero_amount_count: int
    missing_city_count: int
    quality_score: float
    quality_level: str


class DistributionPayload(BaseModel):
    """Frontend-friendly distributions for charts and summaries."""

    status: Dict[str, int]
    payment_method: Dict[str, int]
    merchant_category: Dict[str, int]
    canonical_city: Dict[str, int]
    merchant_canonical_city: Dict[str, int]
    device_type: Dict[str, int]


class TimestampRange(BaseModel):
    """Time range present in the uploaded dataset."""

    min: str
    max: str


class CleaningApiResponse(BaseModel):
    """Response payload returned after a CSV cleaning job completes."""

    file_id: str
    filename: str
    cleaned_filename: str
    download_url: str
    row_count: int
    column_count: int
    columns: List[str]
    quality_metrics: QualityMetrics
    cleaning_actions: Dict[str, str]
    distributions: DistributionPayload
    timestamp_range: TimestampRange
    preview: List[Dict[str, object]]


class ModelMetrics(BaseModel):
    """Compact model metrics for API responses."""

    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float


class ModelArtifact(BaseModel):
    """Artifact metadata for one trained model."""

    model_name: str
    model_path: str
    metrics: ModelMetrics
    confusion_matrix: Dict[str, int]
    fraud_detected_full_dataset: int
    predicted_non_fraud_full_dataset: int
    fraud_rate_full_dataset: float
    predictions_csv: str
    threshold_report_csv: str
    predictions_download_url: str
    threshold_report_download_url: str
    threshold_table: List[Dict[str, float]]
    feature_importance: List[Dict[str, object]]
    top_risky_transactions: List[Dict[str, object]]
    timing: Dict[str, float]


class PredictApiResponse(BaseModel):
    """Response payload returned after cleaning and scoring a CSV upload."""

    file_id: str
    filename: str
    cleaned_filename: str
    cleaned_download_url: str
    dataset_summary: Dict[str, object]
    row_count: int
    column_count: int
    columns: List[str]
    target_column: str
    label_mode: str
    timing: Dict[str, float]
    quality_metrics: QualityMetrics
    cleaning_actions: Dict[str, str]
    distributions: DistributionPayload
    pattern_summary: Dict[str, int]
    top_risky_transactions: List[Dict[str, object]]
    timestamp_range: TimestampRange
    preview: List[Dict[str, object]]
    models: List[ModelArtifact]

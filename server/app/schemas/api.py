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


class DistributionPayload(BaseModel):
    """Frontend-friendly distributions for charts and summaries."""

    status: Dict[str, int]
    payment_method: Dict[str, int]
    merchant_category_top_10: Dict[str, int]
    canonical_city_top_10: Dict[str, int]


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
    distributions: DistributionPayload
    timestamp_range: TimestampRange
    preview: List[Dict[str, object]]

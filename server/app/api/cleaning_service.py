"""Backend cleaning service for standardized transactional output."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from app.core.pipeline import FraudFeatureEngineer
from app.schemas.response import PipelineResult


def run_cleaning_pipeline(csv_path: str, output_path: Optional[str] = None) -> PipelineResult:
    """Run the normalization pipeline and optionally persist the cleaned dataset."""
    dataframe, summary = FraudFeatureEngineer(csv_path=csv_path).run()

    cleaned_columns = [
        "transaction_id",
        "user_id",
        "device_id",
        "device_type",
        "payment_method",
        "merchant_category",
        "status",
        "timestamp",
        "standardized_timestamp",
        "user_location",
        "merchant_location",
        "canonical_city",
        "merchant_canonical_city",
        "transaction_amount",
        "amt",
        "clean_amount",
        "account_balance",
        "ip_address",
        "raw_fraud_label",
        "raw_fraud_reason",
        "user_avg_spend",
        "spend_deviation",
        "is_new_device",
        "txn_count_1min",
        "txn_count_1h",
        "time_diff",
        "prev_status",
        "consecutive_failures",
        "device_user_degree",
        "ip_velocity_all_users",
        "ip_user_degree",
        "is_micro_transaction",
        "failed_to_success_ratio_1h",
        "payment_method_entropy_10m",
        "balance_depletion_ratio",
        "post_txn_balance_danger",
        "amount_to_balance_ratio",
        "is_cross_city",
        "hour",
        "is_odd_hour",
        "is_post_failure_success",
        "anomaly_score",
        "pattern_location_mismatch",
        "pattern_odd_hour_transaction",
        "pattern_high_amount_vs_balance",
        "pattern_unknown_device",
        "pattern_failed_high_value",
        "pattern_ip_risk",
        "pattern_velocity",
        "pattern_post_failure_success",
        "fraud_label",
        "fraud_reason",
    ]

    cleaned_dataframe = dataframe[cleaned_columns].copy()

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cleaned_dataframe.to_csv(output_path, index=False)

    return {
        "rows_processed": int(len(cleaned_dataframe)),
        "columns_produced": list(cleaned_dataframe.columns),
        "summary": summary,
        "dataframe": cleaned_dataframe,
    }


def build_frontend_summary(dataframe) -> Dict[str, object]:
    """Create frontend-friendly metrics and preview data from a cleaned dataset."""
    unknown_device_count = int((dataframe["device_id"] == "UNKNOWN_DEVICE").sum())
    unknown_payment_method_count = int((dataframe["payment_method"] == "unknown_payment_method").sum())
    unknown_merchant_category_count = int((dataframe["merchant_category"] == "unknown_merchant_category").sum())
    invalid_ip_count = int((dataframe["ip_address"] == "0.0.0.0").sum())
    zero_amount_count = int((dataframe["clean_amount"] == 0).sum())
    missing_city_count = int(
        ((dataframe["canonical_city"] == "unknown_city") | (dataframe["merchant_canonical_city"] == "unknown_city")).sum()
    )

    row_count = max(int(len(dataframe)), 1)
    quality_penalty = (
        unknown_device_count
        + unknown_payment_method_count
        + unknown_merchant_category_count
        + invalid_ip_count
        + zero_amount_count
        + missing_city_count
    ) / row_count
    quality_score = round(max(0.0, 100.0 - (quality_penalty * 100.0)), 2)

    if quality_score >= 90:
        quality_level = "good"
    elif quality_score >= 75:
        quality_level = "warning"
    else:
        quality_level = "poor"

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": list(dataframe.columns),
        "preview": dataframe.head(10).to_dict(orient="records"),
        "quality_metrics": {
            "unknown_device_count": unknown_device_count,
            "unknown_payment_method_count": unknown_payment_method_count,
            "unknown_merchant_category_count": unknown_merchant_category_count,
            "invalid_ip_count": invalid_ip_count,
            "zero_amount_count": zero_amount_count,
            "missing_city_count": missing_city_count,
            "quality_score": quality_score,
            "quality_level": quality_level,
        },
        "cleaning_actions": {
            "invalid_ip": "Invalid or malformed IP addresses are replaced with 0.0.0.0.",
            "amount_normalization": "Amounts are parsed from transaction_amount and amt, currency symbols are removed, and invalid values fall back to 0.0.",
            "timestamp_parsing": "Mixed timestamp formats are parsed into standardized_timestamp, and unparseable values fall back to 1970-01-01 00:00:00.",
            "city_normalization": "User and merchant cities are normalized to canonical city names, and unknown values become unknown_city.",
            "device_normalization": "Malformed device IDs are converted to UNKNOWN_DEVICE and unseen devices are tracked with is_new_device.",
            "status_normalization": "Transaction statuses are normalized into success, failed, pending, or unknown_status.",
        },
        "distributions": {
            "status": dataframe["status"].value_counts().to_dict(),
            "payment_method": dataframe["payment_method"].value_counts().to_dict(),
            "merchant_category": dataframe["merchant_category"].value_counts().to_dict(),
            "canonical_city": dataframe["canonical_city"].value_counts().to_dict(),
            "merchant_canonical_city": dataframe["merchant_canonical_city"].value_counts().to_dict(),
            "device_type": dataframe["device_type"].value_counts().to_dict(),
        },
        "timestamp_range": {
            "min": str(dataframe["standardized_timestamp"].min()),
            "max": str(dataframe["standardized_timestamp"].max()),
        },
    }

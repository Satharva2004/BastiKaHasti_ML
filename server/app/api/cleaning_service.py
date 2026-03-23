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
        "is_micro_transaction",
        "failed_to_success_ratio_1h",
        "payment_method_entropy_10m",
        "balance_depletion_ratio",
        "post_txn_balance_danger",
        "is_cross_city",
        "hour",
        "is_odd_hour",
        "anomaly_score",
        "pattern_velocity",
        "pattern_device",
        "pattern_amount",
        "pattern_micro",
        "pattern_failure_burst",
        "pattern_time_gap",
        "fraud_label",
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
    return {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": list(dataframe.columns),
        "preview": dataframe.head(10).to_dict(orient="records"),
        "quality_metrics": {
            "unknown_device_count": int((dataframe["device_id"] == "UNKNOWN_DEVICE").sum()),
            "unknown_payment_method_count": int((dataframe["payment_method"] == "unknown_payment_method").sum()),
            "unknown_merchant_category_count": int((dataframe["merchant_category"] == "unknown_merchant_category").sum()),
            "invalid_ip_count": int((dataframe["ip_address"] == "0.0.0.0").sum()),
            "zero_amount_count": int((dataframe["clean_amount"] == 0).sum()),
        },
        "distributions": {
            "status": dataframe["status"].value_counts().to_dict(),
            "payment_method": dataframe["payment_method"].value_counts().to_dict(),
            "merchant_category_top_10": dataframe["merchant_category"].value_counts().head(10).to_dict(),
            "canonical_city_top_10": dataframe["canonical_city"].value_counts().head(10).to_dict(),
        },
        "timestamp_range": {
            "min": str(dataframe["standardized_timestamp"].min()),
            "max": str(dataframe["standardized_timestamp"].max()),
        },
    }

"""Train safer fraud models from a raw transactional CSV."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

SERVER_DIR = Path(__file__).resolve().parents[2]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from app.core.pipeline import run_pipeline


REAL_LABEL_CANDIDATES = [
    "raw_fraud_label",
    "source_fraud_label",
    "is_fraud",
    "fraud",
    "fraud_flag",
    "label",
    "target",
    "chargeback",
    "chargeback_flag",
    "is_chargeback",
    "confirmed_fraud",
    "is_confirmed_fraud",
]
PROXY_TARGET = "proxy_fraud_label"
BASE_STORAGE_DIR = Path("storage")
CLEANED_DIR = BASE_STORAGE_DIR / "cleaned"
MODEL_DIR = BASE_STORAGE_DIR / "models"
PREDICTIONS_DIR = BASE_STORAGE_DIR / "predictions"
REPORTS_DIR = BASE_STORAGE_DIR / "reports"


def load_and_prep(csv_path: str) -> pd.DataFrame:
    """Load raw CSV data and run the shared cleaning pipeline."""
    print(f"[load] Reading {csv_path} ...")
    dataframe = pd.read_csv(csv_path, low_memory=False)
    print("[load] Running pipeline.py ...")
    dataframe = run_pipeline(dataframe)
    print(f"[load] Final shape: {dataframe.shape}")
    return dataframe


def _select_target(dataframe: pd.DataFrame) -> Tuple[pd.Series, str, str]:
    """Choose a real target if present, otherwise fall back to an honest proxy target."""
    available_columns = {column.lower(): column for column in dataframe.columns}

    for candidate in REAL_LABEL_CANDIDATES:
        original_name = available_columns.get(candidate.lower())
        if not original_name:
            continue
        series = _normalize_binary_label_series(dataframe[original_name])
        if series is None:
            continue
        valid_values = set(series.dropna().astype(int).unique().tolist())
        if valid_values.issubset({0, 1}) and len(valid_values) > 1:
            return series.fillna(0).astype(int), original_name, "real"

    heuristic_label_column = available_columns.get("fraud_label")
    if heuristic_label_column:
        series = _normalize_binary_label_series(dataframe[heuristic_label_column])
        if series is not None:
            valid_values = set(series.dropna().astype(int).unique().tolist())
            if valid_values.issubset({0, 1}) and len(valid_values) > 1:
                return series.fillna(0).astype(int), heuristic_label_column, "proxy"

    proxy_label = (
        (dataframe["pattern_location_mismatch"] == 1)
        | (dataframe["pattern_odd_hour_transaction"] == 1)
        | (dataframe["pattern_high_amount_vs_balance"] == 1)
        | (dataframe["pattern_unknown_device"] == 1)
        | (dataframe["pattern_failed_high_value"] == 1)
    ).astype(int)
    dataframe[PROXY_TARGET] = proxy_label
    return dataframe[PROXY_TARGET], PROXY_TARGET, "proxy"


def _normalize_binary_label_series(series: pd.Series) -> pd.Series | None:
    """Convert common fraud-label formats into a numeric binary series."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() > 0:
        return numeric

    normalized = series.astype(str).str.strip().str.lower()
    mapped = normalized.map(
        {
            "fraud": 1,
            "not fraud": 0,
            "true": 1,
            "false": 0,
            "yes": 1,
            "no": 0,
        }
    )
    if mapped.notna().sum() > 0:
        return mapped

    return None


def _build_feature_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Use lower-leakage features suitable for a first real system iteration."""
    feature_columns = [
        "clean_amount",
        "account_balance",
        "txn_count_1min",
        "txn_count_1h",
        "consecutive_failures",
        "device_user_degree",
        "ip_velocity_all_users",
        "ip_user_degree",
        "payment_method_entropy_10m",
        "balance_depletion_ratio",
        "amount_to_balance_ratio",
        "is_cross_city",
        "hour",
        "is_odd_hour",
        "is_post_failure_success",
        "device_type",
        "payment_method",
        "merchant_category",
        "status",
        "canonical_city",
        "merchant_canonical_city",
    ]
    available_columns = [column for column in feature_columns if column in dataframe.columns]
    return dataframe[available_columns].copy()


def _build_preprocessor(features: pd.DataFrame) -> ColumnTransformer:
    """Build shared preprocessing for model training."""
    numeric_columns = features.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_columns = [column for column in features.columns if column not in numeric_columns]
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_columns,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_columns,
            ),
        ]
    )


def _time_split(
    dataframe: pd.DataFrame,
    features: pd.DataFrame,
    target: pd.Series,
    test_fraction: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Index, pd.Index]:
    """Split chronologically to better match production behavior."""
    sort_columns: List[str] = []
    if "standardized_timestamp" in dataframe.columns:
        sort_columns.append("standardized_timestamp")
    sort_columns.append("transaction_id")

    ordered = dataframe.sort_values(sort_columns, kind="mergesort").reset_index()
    split_index = max(int(len(ordered) * (1 - test_fraction)), 1)
    split_index = min(split_index, len(ordered) - 1)

    train_rows = ordered.iloc[:split_index]["index"]
    test_rows = ordered.iloc[split_index:]["index"]

    X_train = features.loc[train_rows]
    X_test = features.loc[test_rows]
    y_train = target.loc[train_rows]
    y_test = target.loc[test_rows]
    return X_train, X_test, y_train, y_test, train_rows, test_rows


def _compute_metrics(y_true: pd.Series, predictions, probabilities) -> Dict[str, float]:
    """Compute common binary classification metrics."""
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)) if y_true.nunique() > 1 else 0.0,
    }


def _compute_confusion_matrix(y_true: pd.Series, predictions) -> Dict[str, int]:
    """Return confusion-matrix counts in a frontend-friendly shape."""
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def _threshold_sweep(y_true: pd.Series, probabilities) -> pd.DataFrame:
    """Build a compact threshold-performance table for business tuning."""
    rows = []
    for threshold in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        predicted = (probabilities >= threshold).astype(int)
        rows.append(
            {
                "threshold": threshold,
                "predicted_fraud": int(predicted.sum()),
                "precision": float(precision_score(y_true, predicted, zero_division=0)),
                "recall": float(recall_score(y_true, predicted, zero_division=0)),
                "f1": float(f1_score(y_true, predicted, zero_division=0)),
            }
        )
    return pd.DataFrame(rows)


def _extract_feature_importance(pipeline: Pipeline, features_all: pd.DataFrame) -> List[Dict[str, object]]:
    """Extract top feature importances from the fitted model pipeline."""
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    try:
        feature_names = preprocessor.get_feature_names_out()
    except Exception:
        feature_names = [f"feature_{index}" for index in range(len(features_all.columns))]

    if hasattr(classifier, "feature_importances_"):
        importances = classifier.feature_importances_
    elif hasattr(classifier, "coef_"):
        importances = abs(classifier.coef_[0])
    else:
        return []

    pairs = [
        {"feature_name": str(name), "importance_score": float(score)}
        for name, score in zip(feature_names, importances)
    ]
    pairs.sort(key=lambda item: item["importance_score"], reverse=True)
    return pairs[:20]


def _top_risky_transactions(
    dataframe: pd.DataFrame,
    probabilities,
    predictions,
    target: pd.Series,
) -> List[Dict[str, object]]:
    """Return the highest-risk transactions for frontend drill-down."""
    export_columns = [
        "transaction_id",
        "user_id",
        "standardized_timestamp",
        "clean_amount",
        "account_balance",
        "status",
        "canonical_city",
        "merchant_canonical_city",
        "device_type",
        "payment_method",
        "merchant_category",
        "fraud_reason",
        "pattern_location_mismatch",
        "pattern_odd_hour_transaction",
        "pattern_high_amount_vs_balance",
        "pattern_unknown_device",
        "pattern_failed_high_value",
        "pattern_ip_risk",
        "pattern_velocity",
        "pattern_post_failure_success",
    ]
    available_columns = [column for column in export_columns if column in dataframe.columns]
    risky = dataframe[available_columns].copy()
    risky["actual_label"] = target.astype(int).values
    risky["predicted_label"] = predictions.astype(int)
    risky["fraud_probability"] = probabilities.round(6)
    risky = risky.sort_values("fraud_probability", ascending=False).head(25)
    return risky.to_dict(orient="records")


def _save_predictions_csv(
    dataframe: pd.DataFrame,
    model_name: str,
    probabilities,
    predictions,
    target: pd.Series,
    artifact_stem: str,
) -> Path:
    """Persist row-level scores for manual review and threshold tuning."""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PREDICTIONS_DIR / f"{artifact_stem}_{model_name}_predictions.csv"

    export_columns = [
        "transaction_id",
        "user_id",
        "standardized_timestamp",
        "clean_amount",
        "canonical_city",
        "merchant_canonical_city",
        "device_type",
        "payment_method",
        "merchant_category",
        "status",
    ]
    available_columns = [column for column in export_columns if column in dataframe.columns]
    predictions_frame = dataframe[available_columns].copy()
    predictions_frame["actual_label"] = target.astype(int).values
    predictions_frame["predicted_label"] = predictions.astype(int)
    predictions_frame["fraud_probability"] = probabilities.round(6)
    predictions_frame.sort_values("fraud_probability", ascending=False).to_csv(output_path, index=False)
    return output_path


def _save_threshold_report(artifact_stem: str, model_name: str, threshold_table: pd.DataFrame) -> Path:
    """Persist threshold choices for later product decisions."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"{artifact_stem}_{model_name}_thresholds.csv"
    threshold_table.to_csv(output_path, index=False)
    return output_path


def _train_single_model(
    model_name: str,
    estimator,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    features_all: pd.DataFrame,
    target_all: pd.Series,
    dataframe_all: pd.DataFrame,
    source_csv: Path,
    artifact_stem: str,
    target_name: str,
    label_mode: str,
) -> Dict[str, Any]:
    """Fit, evaluate, persist, and summarize one model."""
    train_started = perf_counter()
    pipeline = Pipeline(
        steps=[
            ("preprocessor", _build_preprocessor(features_all)),
            ("classifier", estimator),
        ]
    )
    pipeline.fit(X_train, y_train)
    training_duration_ms = round((perf_counter() - train_started) * 1000, 2)

    scoring_started = perf_counter()
    test_predictions = pipeline.predict(X_test)
    test_probabilities = pipeline.predict_proba(X_test)[:, 1]
    full_probabilities = pipeline.predict_proba(features_all)[:, 1]
    full_predictions = (full_probabilities >= 0.5).astype(int)
    prediction_duration_ms = round((perf_counter() - scoring_started) * 1000, 2)

    metrics = _compute_metrics(y_test, test_predictions, test_probabilities)
    confusion = _compute_confusion_matrix(y_test, test_predictions)
    fraud_detected = int(full_predictions.sum())
    threshold_table = _threshold_sweep(y_test, test_probabilities)
    feature_importance = _extract_feature_importance(pipeline, features_all)
    top_risky = _top_risky_transactions(dataframe_all, full_probabilities, full_predictions, target_all)
    threshold_report_path = _save_threshold_report(artifact_stem, model_name, threshold_table)
    predictions_path = _save_predictions_csv(
        dataframe=dataframe_all,
        model_name=model_name,
        probabilities=full_probabilities,
        predictions=full_predictions,
        target=target_all,
        artifact_stem=artifact_stem,
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / f"{artifact_stem}_{model_name}.joblib"
    joblib.dump(
        {
            "model_name": model_name,
            "model": pipeline,
            "metrics": metrics,
            "fraud_detected_full_dataset": fraud_detected,
            "feature_columns": list(features_all.columns),
            "target_column": target_name,
            "label_mode": label_mode,
            "source_csv": str(source_csv),
            "predictions_csv": str(predictions_path),
            "confusion_matrix": confusion,
            "feature_importance": feature_importance,
            "threshold_table": threshold_table.to_dict(orient="records"),
            "top_risky_transactions": top_risky,
        },
        model_path,
    )

    print(f"[train:{model_name}] Model saved to {model_path}")
    print(f"[train:{model_name}] Metrics: {metrics}")
    print(f"[train:{model_name}] Fraud predicted on full dataset: {fraud_detected}")
    print(f"[train:{model_name}] Predictions CSV: {predictions_path}")
    print(f"[train:{model_name}] Threshold report: {threshold_report_path}")
    return {
        "model_name": model_name,
        "model_path": str(model_path),
        "metrics": metrics,
        "confusion_matrix": confusion,
        "fraud_detected_full_dataset": fraud_detected,
        "predicted_non_fraud_full_dataset": int(len(full_predictions) - fraud_detected),
        "fraud_rate_full_dataset": float(fraud_detected / len(full_predictions)),
        "predictions_csv": str(predictions_path),
        "threshold_report_csv": str(threshold_report_path),
        "threshold_table": threshold_table.to_dict(orient="records"),
        "feature_importance": feature_importance,
        "top_risky_transactions": top_risky,
        "timing": {
            "training_duration_ms": training_duration_ms,
            "prediction_duration_ms": prediction_duration_ms,
            "total_model_duration_ms": round(training_duration_ms + prediction_duration_ms, 2),
        },
    }


def train(csv_path: str, artifact_prefix: str | None = None) -> Dict[str, Any]:
    """Clean raw data, save the cleaned export, and train safer tree models."""
    total_started = perf_counter()
    source_csv = Path(csv_path)
    artifact_stem = artifact_prefix or source_csv.stem
    cleaning_started = perf_counter()
    dataframe = load_and_prep(str(source_csv))
    cleaning_duration_ms = round((perf_counter() - cleaning_started) * 1000, 2)
    target, target_name, label_mode = _select_target(dataframe)

    print(f"[target] Using '{target_name}' as the training target ({label_mode} label mode).")
    print(f"[target] Distribution:\n{target.value_counts(dropna=False)}")
    if label_mode == "proxy":
        print("[target] No real fraud label was found in the CSV, so this run uses a proxy alert target.")

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_csv_path = _build_cleaned_output_path(artifact_stem)
    dataframe.to_csv(cleaned_csv_path, index=False)
    print(f"[clean] Cleaned CSV saved to {cleaned_csv_path}")

    features = _build_feature_frame(dataframe)
    X_train, X_test, y_train, y_test, _, _ = _time_split(dataframe, features, target)

    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    model_results = []
    model_results.append(
        _train_single_model(
            model_name="random_forest",
            estimator=RandomForestClassifier(
                n_estimators=400,
                random_state=42,
                class_weight="balanced",
                min_samples_leaf=5,
                max_depth=12,
                min_samples_split=10,
                n_jobs=-1,
            ),
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            features_all=features,
            target_all=target,
            dataframe_all=dataframe,
            source_csv=source_csv,
            artifact_stem=artifact_stem,
            target_name=target_name,
            label_mode=label_mode,
        )
    )
    model_results.append(
        _train_single_model(
            model_name="xgboost",
            estimator=XGBClassifier(
                n_estimators=450,
                max_depth=5,
                learning_rate=0.03,
                subsample=0.75,
                colsample_bytree=0.75,
                min_child_weight=5,
                gamma=1.0,
                reg_lambda=4.0,
                reg_alpha=0.5,
                eval_metric="logloss",
                random_state=42,
                scale_pos_weight=scale_pos_weight,
            ),
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            features_all=features,
            target_all=target,
            dataframe_all=dataframe,
            source_csv=source_csv,
            artifact_stem=artifact_stem,
            target_name=target_name,
            label_mode=label_mode,
        )
    )

    return {
        "source_csv": str(source_csv),
        "cleaned_csv_path": str(cleaned_csv_path),
        "rows_used": int(len(dataframe)),
        "feature_count": int(features.shape[1]),
        "target_column": target_name,
        "label_mode": label_mode,
        "timing": {
            "cleaning_duration_ms": cleaning_duration_ms,
            "total_duration_ms": round((perf_counter() - total_started) * 1000, 2),
        },
        "models": model_results,
    }


def _build_cleaned_output_path(artifact_stem: str) -> Path:
    """Generate a unique cleaned CSV path for each run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return CLEANED_DIR / f"{artifact_stem}_cleaned_{timestamp}.csv"


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI."""
    parser = argparse.ArgumentParser(description="Train safer fraud models from a raw transaction CSV.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="app/sample.csv",
        help="Path to the raw CSV. Defaults to app/sample.csv.",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    args = build_parser().parse_args()
    result = train(args.csv_path)
    print(result)


if __name__ == "__main__":
    main()

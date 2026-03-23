"""Train safer fraud models from a raw transactional CSV."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

SERVER_DIR = Path(__file__).resolve().parents[2]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from app.core.pipeline import run_pipeline


REAL_LABEL_CANDIDATES = [
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
        series = pd.to_numeric(dataframe[original_name], errors="coerce")
        if series.notna().sum() == 0:
            continue
        valid_values = set(series.dropna().astype(int).unique().tolist())
        if valid_values.issubset({0, 1}) and len(valid_values) > 1:
            return series.fillna(0).astype(int), original_name, "real"

    heuristic_label_column = available_columns.get("fraud_label")
    if heuristic_label_column:
        series = pd.to_numeric(dataframe[heuristic_label_column], errors="coerce")
        valid_values = set(series.dropna().astype(int).unique().tolist())
        if valid_values.issubset({0, 1}) and len(valid_values) > 1:
            return series.fillna(0).astype(int), heuristic_label_column, "proxy"

    proxy_label = (
        (dataframe["txn_count_1min"] > 5)
        | (dataframe["device_user_degree"] > 3)
        | (dataframe["consecutive_failures"] >= 3)
        | ((dataframe["is_cross_city"] == 1) & (dataframe["is_odd_hour"] == 1))
        | (
            (dataframe["clean_amount"] > dataframe["user_avg_spend"].fillna(0) * 3)
            & (dataframe["clean_amount"] > 0)
        )
    ).astype(int)
    dataframe[PROXY_TARGET] = proxy_label
    return dataframe[PROXY_TARGET], PROXY_TARGET, "proxy"


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
        "payment_method_entropy_10m",
        "balance_depletion_ratio",
        "is_cross_city",
        "hour",
        "is_odd_hour",
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


def _save_predictions_csv(
    dataframe: pd.DataFrame,
    model_name: str,
    probabilities,
    predictions,
    target: pd.Series,
    source_csv: Path,
) -> Path:
    """Persist row-level scores for manual review and threshold tuning."""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PREDICTIONS_DIR / f"{source_csv.stem}_{model_name}_predictions.csv"

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
    target_name: str,
    label_mode: str,
) -> Dict[str, Any]:
    """Fit, evaluate, persist, and summarize one model."""
    pipeline = Pipeline(
        steps=[
            ("preprocessor", _build_preprocessor(features_all)),
            ("classifier", estimator),
        ]
    )
    pipeline.fit(X_train, y_train)

    test_predictions = pipeline.predict(X_test)
    test_probabilities = pipeline.predict_proba(X_test)[:, 1]
    full_probabilities = pipeline.predict_proba(features_all)[:, 1]
    full_predictions = pipeline.predict(features_all)

    metrics = _compute_metrics(y_test, test_predictions, test_probabilities)
    fraud_detected = int(full_predictions.sum())
    predictions_path = _save_predictions_csv(
        dataframe=dataframe_all,
        model_name=model_name,
        probabilities=full_probabilities,
        predictions=full_predictions,
        target=target_all,
        source_csv=source_csv,
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / f"{source_csv.stem}_{model_name}.joblib"
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
        },
        model_path,
    )

    print(f"[train:{model_name}] Model saved to {model_path}")
    print(f"[train:{model_name}] Metrics: {metrics}")
    print(f"[train:{model_name}] Fraud predicted on full dataset: {fraud_detected}")
    print(f"[train:{model_name}] Predictions CSV: {predictions_path}")
    return {
        "model_name": model_name,
        "model_path": str(model_path),
        "metrics": metrics,
        "fraud_detected_full_dataset": fraud_detected,
        "predictions_csv": str(predictions_path),
    }


def train(csv_path: str) -> Dict[str, Any]:
    """Clean raw data, save the cleaned export, and train safer tree models."""
    source_csv = Path(csv_path)
    dataframe = load_and_prep(str(source_csv))
    target, target_name, label_mode = _select_target(dataframe)

    print(f"[target] Using '{target_name}' as the training target ({label_mode} label mode).")
    print(f"[target] Distribution:\n{target.value_counts(dropna=False)}")
    if label_mode == "proxy":
        print("[target] No real fraud label was found in the CSV, so this run uses a proxy alert target.")

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_csv_path = _build_cleaned_output_path(source_csv)
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
                n_estimators=300,
                random_state=42,
                class_weight="balanced",
                min_samples_leaf=3,
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
            target_name=target_name,
            label_mode=label_mode,
        )
    )
    model_results.append(
        _train_single_model(
            model_name="xgboost",
            estimator=XGBClassifier(
                n_estimators=250,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                reg_lambda=2.0,
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
        "models": model_results,
    }


def _build_cleaned_output_path(source_csv: Path) -> Path:
    """Generate a unique cleaned CSV path for each run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return CLEANED_DIR / f"{source_csv.stem}_cleaned_{timestamp}.csv"


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

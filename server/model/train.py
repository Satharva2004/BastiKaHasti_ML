import argparse
import os
import pickle

import lightgbm as lgb
import pandas as pd
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split

from model.features import build_feature_matrix


def ensure_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic labels for development if none exist."""
    df = df.copy()
    if "is_fraud" not in df.columns:
        df["is_fraud"] = (
            (df["feat_amount_zscore"].abs() > 3)
            & ((df["feat_geo_deviation"] == 1) | (df["feat_new_device"] == 1))
        ).astype(int)
    return df


def train(data_path: str, model_out: str = "data/models/lgbm_model.pkl"):
    df = pd.read_csv(data_path)
    df = ensure_labels(df)
    X, y = build_feature_matrix(df)

    if y is None:
        raise ValueError("Training requires a target column or synthetic-label generation.")
    if y.nunique() < 2:
        raise ValueError("Training target has fewer than two classes after label preparation.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = lgb.LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=31,
        class_weight="balanced",
        random_state=42,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred)
    score = f1_score(y_test, y_pred)

    os.makedirs(os.path.dirname(model_out), exist_ok=True)
    with open(model_out, "wb") as f:
        pickle.dump(model, f)

    print(report)
    print(f"F1 score: {score:.4f}")
    print(f"Model saved to {model_out}")

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/pipeline_output.csv")
    parser.add_argument("--model-out", default="data/models/lgbm_model.pkl")
    args = parser.parse_args()
    train(args.data, args.model_out)

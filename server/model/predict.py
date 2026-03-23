import argparse
import pickle

import pandas as pd

from model.explain import compute_shap_matrix, serialise_shap_rows
from model.features import build_feature_matrix


def load_model(path: str = "data/models/lgbm_model.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)


def predict_with_shap(df: pd.DataFrame, model) -> pd.DataFrame:
    """
    Return df with added fraud scores and SHAP explanations.
    """
    df = df.copy()
    X, _ = build_feature_matrix(df)

    df["fraud_probability"] = model.predict_proba(X)[:, 1]
    df["fraud_label"] = (df["fraud_probability"] >= 0.5).astype(int)
    df["shap_values"] = serialise_shap_rows(compute_shap_matrix(model, X))

    return df


def main(data_path: str, model_path: str, output_path: str):
    df = pd.read_csv(data_path)
    model = load_model(model_path)
    predictions = predict_with_shap(df, model)
    predictions.to_csv(output_path, index=False)
    print(f"Predictions written to {output_path}")
    print(f"Rows scored: {len(predictions)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/pipeline_output.csv")
    parser.add_argument("--model", default="data/models/lgbm_model.pkl")
    parser.add_argument("--output", default="data/processed/final_output.csv")
    args = parser.parse_args()
    main(args.data, args.model, args.output)

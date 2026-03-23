import json

import shap

from model.features import FEATURE_COLS


def build_tree_explainer(model):
    """Create a SHAP TreeExplainer for the trained model."""
    return shap.TreeExplainer(model)


def compute_shap_matrix(model, X):
    """Return the SHAP matrix for the fraud class."""
    explainer = build_tree_explainer(model)
    shap_vals = explainer.shap_values(X)

    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]

    return shap_vals


def serialise_shap_rows(shap_matrix):
    """Convert SHAP rows into JSON strings keyed by feature name."""
    return [
        json.dumps(dict(zip(FEATURE_COLS, [round(float(v), 4) for v in row])))
        for row in shap_matrix
    ]

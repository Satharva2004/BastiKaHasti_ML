FEATURE_COLS = [
    "feat_amount_zscore",
    "feat_geo_deviation",
    "feat_new_device",
    "feat_new_payment",
    "feat_hour_zscore",
    "feat_velocity_ratio",
    "feat_new_category",
    "feat_category_zscore",
    "hour_of_day",
    "day_of_week",
    "dna_txn_count",
]

TARGET_COL = "is_fraud"


def build_feature_matrix(df):
    """Return feature matrix X and optional target y."""
    X = df[FEATURE_COLS].fillna(0)
    y = df[TARGET_COL] if TARGET_COL in df.columns else None
    return X, y

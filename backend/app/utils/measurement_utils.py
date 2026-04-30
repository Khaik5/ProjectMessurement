import pandas as pd

from app.ml.feature_engineering import build_p7_features


def compute_measurement_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return build_p7_features(df, use_label_density=True)


def measurement_fallback_message(used_active_model: bool) -> str | None:
    if used_active_model:
        return None
    return "Used measurement-based fallback because no active ML model exists."

import pandas as pd

from app.ml.feature_engineering import build_p7_features


def compute_measurement_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return build_p7_features(df, use_label_density=False, use_defect_count_density=False)


def measurement_fallback_message(used_active_model: bool, reason: str | None = None) -> str | None:
    if used_active_model:
        return None
    if reason:
        return f"Used measurement-based fallback ({reason})."
    return "Used measurement-based fallback because no active ML model exists."

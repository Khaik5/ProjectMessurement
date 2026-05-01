from __future__ import annotations

LABEL_COLUMN = "defect_label"

RAW_INPUT_COLUMNS = [
    "module_name",
    "loc",
    "ncloc",
    "cloc",
    "complexity",
    "cyclomatic_complexity",
    "depth_of_nesting",
    "coupling",
    "cohesion",
    "information_flow_complexity",
    "code_churn",
    "change_request_backlog",
    "pending_effort_hours",
    "percent_reused",
]

DERIVED_FEATURE_COLUMNS = [
    "kloc",
    "comment_ratio",
    "defect_density",
    "size_score",
    "complexity_score",
    "coupling_score",
    "churn_score",
    "cohesion_score",
    "reuse_score",
    "risk_score",
]

ENGINEERED_OUTPUT_COLUMNS = [
    "loc",
    "ncloc",
    "cloc",
    "kloc",
    "comment_ratio",
    "complexity",
    "cyclomatic_complexity",
    "depth_of_nesting",
    "coupling",
    "cohesion",
    "information_flow_complexity",
    "code_churn",
    "change_request_backlog",
    "pending_effort_hours",
    "percent_reused",
    "defect_density",
    "size_score",
    "complexity_score",
    "coupling_score",
    "churn_score",
    "cohesion_score",
    "reuse_score",
    "risk_score",
]

EXCLUDED_LEAKAGE_COLUMNS = [
    LABEL_COLUMN,
    "prediction",
    "prediction_label",
    "risk_level",
    "actual_defects",
    "bug_count",
    "defect_count",
    "defect_density",
    "fixed_defects",
    "historical_defects",
    "post_release_defects",
]

EXCLUDED_MODEL_COLUMNS = [
    "defect_density",
    "risk_score",
]

SAFE_MODEL_FEATURE_COLUMNS = [
    column for column in ENGINEERED_OUTPUT_COLUMNS if column not in set(EXCLUDED_LEAKAGE_COLUMNS + EXCLUDED_MODEL_COLUMNS)
]

MODEL_FEATURE_SCHEMA_VERSION = 2


def assert_safe_model_features(feature_columns: list[str]) -> None:
    forbidden = set(EXCLUDED_LEAKAGE_COLUMNS + EXCLUDED_MODEL_COLUMNS)
    leaked = [column for column in feature_columns if column in forbidden]
    if leaked:
        raise ValueError(f"Unsafe model feature columns detected: {', '.join(leaked)}")
    if list(feature_columns) != SAFE_MODEL_FEATURE_COLUMNS:
        raise ValueError("Model feature columns do not match SAFE_MODEL_FEATURE_COLUMNS order.")

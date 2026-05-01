import pandas as pd

from app.ml.feature_engineering import P7_FEATURE_COLUMNS

REQUIRED_MIN_COLUMNS = ["loc", "complexity", "coupling"]

# Minimal required (one of module_name/module_path) + core numeric features
REQUIRED_COLUMNS = ["module_name", "loc", "complexity", "coupling", "code_churn"]
TRAINING_COLUMNS = [*REQUIRED_COLUMNS, "defect_label"]

# Full set used for ML training/prediction (missing columns will be filled later)
FEATURE_COLUMNS = P7_FEATURE_COLUMNS

OPTIONAL_COLUMNS = [
    "module_path",
    "ncloc",
    "cloc",
    "cyclomatic_complexity",
    "depth_of_nesting",
    "cohesion",
    "information_flow_complexity",
    "change_request_backlog",
    "pending_effort_hours",
    "percent_reused",
    "defect_count",
    "defect_label",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "loc": "loc",
        "LOC": "loc",
        "Module": "module_name",
        "module": "module_name",
        "path": "module_path",
        "module_path": "module_path",
        "churn": "code_churn",
        "codeChurn": "code_churn",
        "codechurn": "code_churn",
        "code churn": "code_churn",
        "label": "defect_label",
        "defect": "defect_label",
        "defects": "defect_count",
        "defectCount": "defect_count",
        "defectcount": "defect_count",
        "nCLOC": "ncloc",
        "NCLOC": "ncloc",
        "CLOC": "cloc",
        "cyclomatic": "cyclomatic_complexity",
        "cyclomaticComplexity": "cyclomatic_complexity",
        "cyclomaticcomplexity": "cyclomatic_complexity",
        "depth": "depth_of_nesting",
        "nesting_depth": "depth_of_nesting",
        "ifc": "information_flow_complexity",
        "informationFlowComplexity": "information_flow_complexity",
        "informationflowcomplexity": "information_flow_complexity",
        "reuse_percent": "percent_reused",
        "percentReuse": "percent_reused",
        "percentreuse": "percent_reused",
        "backlog": "change_request_backlog",
        "pending_effort": "pending_effort_hours",
    }
    normalized = {}
    for column in df.columns:
        clean = str(column).strip()
        normalized[column] = aliases.get(clean, aliases.get(clean.lower(), clean))
    return df.rename(columns=normalized)


def validate_metrics_dataframe(df: pd.DataFrame, require_label: bool = False) -> tuple[bool, list[str], pd.DataFrame]:
    df = normalize_columns(df.copy())
    errors: list[str] = []

    # module_name/module_path
    if "module_name" not in df.columns and "module_path" in df.columns:
        df["module_name"] = df["module_path"]
    if "module_name" not in df.columns:
        errors.append("Missing columns: module_name (or module_path)")

    # Convert numeric columns if present
    numeric_candidates = [
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
        "defect_count",
        "defect_label",
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Required numeric columns
    if "loc" in df.columns:
        if df["loc"].isna().any():
            errors.append("loc must be numeric")
        if (df["loc"].dropna() < 0).any():
            errors.append("loc must be >= 0")
    else:
        errors.append("Missing columns: loc")

    for col in ["complexity", "coupling"]:
        if col not in df.columns:
            errors.append(f"Missing columns: {col}")
        else:
            if df[col].isna().any():
                errors.append(f"{col} must be numeric")
            if (df[col].dropna() < 0).any():
                errors.append(f"{col} must be >= 0")

    non_negative_optional = [
        "ncloc",
        "cloc",
        "cyclomatic_complexity",
        "depth_of_nesting",
        "information_flow_complexity",
        "change_request_backlog",
        "pending_effort_hours",
        "defect_count",
    ]
    for col in non_negative_optional:
        if col in df.columns and (df[col].dropna() < 0).any():
            errors.append(f"{col} must be >= 0")

    for col in ["cohesion", "percent_reused"]:
        if col in df.columns:
            values = df[col].dropna()
            if (values < 0).any() or (values > 100).any():
                errors.append(f"{col} must be in [0,1] or [0,100]")

    # ncloc/cloc defaults
    if "ncloc" not in df.columns and "loc" in df.columns:
        df["ncloc"] = df["loc"]
    if "cloc" not in df.columns:
        df["cloc"] = 0

    # cyclomatic_complexity default from complexity
    if "cyclomatic_complexity" not in df.columns and "complexity" in df.columns:
        df["cyclomatic_complexity"] = df["complexity"]

    # code_churn rules
    if "code_churn" not in df.columns or df["code_churn"].isna().all():
        has_backlog = "change_request_backlog" in df.columns and df["change_request_backlog"].notna().any()
        has_effort = "pending_effort_hours" in df.columns and df["pending_effort_hours"].notna().any()
        if has_backlog or has_effort:
            backlog = df["change_request_backlog"].fillna(0) if "change_request_backlog" in df.columns else pd.Series([0.0] * len(df))
            effort = df["pending_effort_hours"].fillna(0) if "pending_effort_hours" in df.columns else pd.Series([0.0] * len(df))
            # simple churn proxy: backlog + 2*effort hours (keeps scale reasonable)
            df["code_churn"] = (backlog.astype(float) + (effort.astype(float) * 2.0)).astype(float)
        else:
            errors.append("Missing columns: code_churn (or change_request_backlog/pending_effort_hours to derive it)")
    else:
        if df["code_churn"].isna().any():
            errors.append("code_churn must be numeric")
        if (df["code_churn"].dropna() < 0).any():
            errors.append("code_churn must be >= 0")

    # defect_label validation
    if "defect_label" in df.columns:
        labels = df["defect_label"]
        if labels.notna().any() and labels.isna().any():
            errors.append("defect_label must be present for all rows or omitted for prediction-only datasets")
        if labels.notna().any() and not bool(labels.dropna().isin([0, 1]).all()):
            errors.append("defect_label must be 0 or 1")

    if require_label and ("defect_label" not in df.columns or not df["defect_label"].notna().any()):
        errors.append("Training requires defect_label column with values 0/1")

    # Ensure module_name string
    if "module_name" in df.columns:
        df["module_name"] = df["module_name"].astype(str)

    return not errors, errors, df

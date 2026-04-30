from __future__ import annotations

import math
from typing import Iterable

import pandas as pd

P7_FEATURE_COLUMNS = [
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

OPTIONAL_P7_COLUMNS = [
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

NORMALIZATION_CAPS = {
    "loc": 2500.0,
    "complexity": 80.0,
    "coupling": 35.0,
    "churn": 800.0,
    "defect_density": 20.0,
}


def _numeric(series: pd.Series | None, default: float = 0.0) -> pd.Series:
    if series is None:
        return pd.Series(dtype="float64")
    return pd.to_numeric(series, errors="coerce").fillna(default).astype(float)


def _clip01(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float).clip(lower=0.0, upper=1.0)


def _normalize(series: pd.Series, cap: float) -> pd.Series:
    if not math.isfinite(cap) or cap <= 0:
        cap = 1.0
    return _clip01(_numeric(series) / cap)


def _normalize_percent(series: pd.Series) -> pd.Series:
    values = _numeric(series)
    if len(values) and float(values.max()) <= 1.0:
        return _clip01(values)
    return _clip01(values / 100.0)


def _records_to_dataframe(records: Iterable[dict] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(records, pd.DataFrame):
        return records.copy()
    return pd.DataFrame(list(records))


def build_p7_features(records: Iterable[dict] | pd.DataFrame, *, use_label_density: bool = False) -> pd.DataFrame:
    """
    Build the fixed P7 measurement feature set.

    `use_label_density=False` is intentional for ML training and prediction. A defect_label-derived
    defect_density is useful for descriptive measurement reports, but feeding it into the model would
    leak the target and can produce misleading 100% scores.
    """
    df = _records_to_dataframe(records)
    if df.empty:
        return pd.DataFrame(columns=["module_name", *P7_FEATURE_COLUMNS])

    out = df.copy()
    if "module_name" not in out.columns and "module_path" in out.columns:
        out["module_name"] = out["module_path"]
    if "module_name" not in out.columns:
        out["module_name"] = [f"module_{idx + 1}" for idx in range(len(out))]

    def col(name: str, default: float = 0.0) -> pd.Series:
        if name in out.columns:
            return _numeric(out[name], default=default)
        return pd.Series([default] * len(out), index=out.index, dtype="float64")

    loc = col("loc")
    out["loc"] = loc.round().astype(int).clip(lower=0)
    out["ncloc"] = col("ncloc", default=math.nan).fillna(loc).round().astype(int).clip(lower=0)
    out["cloc"] = col("cloc").round().astype(int).clip(lower=0)
    out["kloc"] = (loc / 1000.0).clip(lower=0.0)
    out["comment_ratio"] = (out["cloc"].astype(float) / loc.replace(0, pd.NA)).fillna(0.0).clip(lower=0.0, upper=1.0)

    complexity = col("complexity")
    cyclomatic = col("cyclomatic_complexity", default=math.nan).fillna(complexity)
    effective_complexity = pd.concat([complexity, cyclomatic], axis=1).max(axis=1)
    out["complexity"] = complexity
    out["cyclomatic_complexity"] = cyclomatic
    out["depth_of_nesting"] = col("depth_of_nesting")
    out["coupling"] = col("coupling")
    out["cohesion"] = col("cohesion")
    out["information_flow_complexity"] = col("information_flow_complexity")
    out["code_churn"] = col("code_churn")
    out["change_request_backlog"] = col("change_request_backlog")
    out["pending_effort_hours"] = col("pending_effort_hours")
    out["percent_reused"] = col("percent_reused")

    if "defect_count" in out.columns:
        defect_base = col("defect_count", default=math.nan)
    elif use_label_density and "defect_label" in out.columns:
        defect_base = col("defect_label", default=math.nan)
    else:
        defect_base = pd.Series([0.0] * len(out), index=out.index)
    out["defect_density"] = (defect_base.fillna(0.0) / out["kloc"].replace(0, 0.001)).replace([math.inf, -math.inf], 0.0)

    churn_raw = out["code_churn"] + out["change_request_backlog"] * 2.0 + out["pending_effort_hours"] * 0.1

    out["size_score"] = _normalize(out["loc"], NORMALIZATION_CAPS["loc"])
    out["complexity_score"] = _normalize(effective_complexity, NORMALIZATION_CAPS["complexity"])
    out["coupling_score"] = _normalize(out["coupling"], NORMALIZATION_CAPS["coupling"])
    out["churn_score"] = _normalize(churn_raw, NORMALIZATION_CAPS["churn"])
    out["cohesion_score"] = _normalize_percent(out["cohesion"])
    out["reuse_score"] = _normalize_percent(out["percent_reused"])
    defect_density_score = _normalize(out["defect_density"], NORMALIZATION_CAPS["defect_density"])

    risk_score = (
        0.25 * out["size_score"]
        + 0.30 * out["complexity_score"]
        + 0.20 * out["coupling_score"]
        + 0.20 * out["churn_score"]
        + 0.05 * defect_density_score
        - 0.05 * out["cohesion_score"]
        - 0.03 * out["reuse_score"]
    )
    out["risk_score"] = _clip01(risk_score)

    for column in P7_FEATURE_COLUMNS:
        if column not in out.columns:
            out[column] = 0.0

    return out

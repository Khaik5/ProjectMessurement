from __future__ import annotations

import math
import logging
from typing import Iterable

import numpy as np
import pandas as pd

from app.ml.feature_contract import ENGINEERED_OUTPUT_COLUMNS

logger = logging.getLogger(__name__)

P7_FEATURE_COLUMNS = ENGINEERED_OUTPUT_COLUMNS

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

OPTIONAL_P7_INPUT_COLUMNS = [
    "ncloc",
    "cloc",
    "cyclomatic_complexity",
    "depth_of_nesting",
    "cohesion",
    "information_flow_complexity",
    "change_request_backlog",
    "pending_effort_hours",
    "percent_reused",
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
    normalized = values.where(values <= 1.0, values / 100.0)
    return _clip01(normalized)


def _records_to_dataframe(records: Iterable[dict] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(records, pd.DataFrame):
        return records.copy()
    return pd.DataFrame(list(records))


def build_p7_features(
    records: Iterable[dict] | pd.DataFrame,
    *,
    use_label_density: bool = False,
    use_defect_count_density: bool = False,
) -> pd.DataFrame:
    """
    Build the fixed P7 measurement feature set.

    `use_label_density=False` is intentional for ML training and prediction.
    `use_defect_count_density=False` is also intentional by default. Only enable it
    when defect_count is confirmed to be historical information available before
    the prediction point; otherwise it can leak future outcome information.
    """
    df = _records_to_dataframe(records)
    if df.empty:
        return pd.DataFrame(columns=["module_name", *P7_FEATURE_COLUMNS])

    out = df.copy()
    missing_optional = [column for column in OPTIONAL_P7_INPUT_COLUMNS if column not in out.columns]
    warnings = []
    if missing_optional:
        message = f"Missing optional P7 columns filled with defaults: {', '.join(missing_optional)}"
        warnings.append(message)
        logger.warning(message)

    if "module_name" not in out.columns and "module_path" in out.columns:
        out["module_name"] = out["module_path"]
    if "module_name" not in out.columns:
        out["module_name"] = [f"module_{idx + 1}" for idx in range(len(out))]

    def col(name: str, default: float = 0.0) -> pd.Series:
        if name in out.columns:
            return _numeric(out[name], default=default)
        return pd.Series([default] * len(out), index=out.index, dtype="float64")

    loc = col("loc").clip(lower=0.0)
    out["loc"] = loc.round().astype(int).clip(lower=0)
    loc = out["loc"].astype(float)
    out["ncloc"] = col("ncloc", default=math.nan).fillna(loc).round().astype(int).clip(lower=0)
    out["cloc"] = col("cloc").round().astype(int).clip(lower=0)
    out["kloc"] = (loc / 1000.0).clip(lower=0.0)
    comment_ratio = np.divide(
        out["cloc"].astype(float).to_numpy(),
        loc.to_numpy(),
        out=np.zeros(len(out), dtype=float),
        where=loc.to_numpy() != 0,
    )
    out["comment_ratio"] = pd.Series(comment_ratio, index=out.index).clip(lower=0.0, upper=1.0)

    complexity = col("complexity")
    cyclomatic = col("cyclomatic_complexity", default=math.nan).fillna(complexity)
    effective_complexity = pd.concat([complexity, cyclomatic], axis=1).max(axis=1)
    cohesion = _normalize_percent(col("cohesion"))
    percent_reused = _normalize_percent(col("percent_reused"))
    out["complexity"] = complexity
    out["cyclomatic_complexity"] = cyclomatic
    out["depth_of_nesting"] = col("depth_of_nesting")
    out["coupling"] = col("coupling")
    out["cohesion"] = cohesion
    out["information_flow_complexity"] = col("information_flow_complexity")
    out["code_churn"] = col("code_churn")
    out["change_request_backlog"] = col("change_request_backlog")
    out["pending_effort_hours"] = col("pending_effort_hours")
    out["percent_reused"] = percent_reused

    if use_defect_count_density and "defect_count" in out.columns:
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
    out["cohesion_score"] = out["cohesion"]
    out["reuse_score"] = out["percent_reused"]
    defect_density_score = _normalize(out["defect_density"], NORMALIZATION_CAPS["defect_density"])
    out["defect_density_score"] = defect_density_score

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

    out.attrs["warnings"] = warnings
    return out

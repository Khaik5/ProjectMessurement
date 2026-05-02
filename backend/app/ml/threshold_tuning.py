from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)

THRESHOLD_STRATEGIES = {
    "balanced_f1_with_recall_floor",
    "recall_priority",
    "precision_priority",
    "best_f1",
    "custom",
}

TRAINING_PROFILES = {
    "balanced_production",
    "high_recall",
    "high_precision",
    "best_roc_auc",
    "best_pr_auc",
    "custom",
}

PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "balanced_production": {
        "strategy": "balanced_f1_with_recall_floor",
        "recall_floor": 0.80,
        "precision_floor": 0.70,
        "beta": 1.3,
        "threshold_min": 0.20,
        "threshold_max": 0.80,
        "threshold_step": 0.01,
        "best_model_metric": "f1",
    },
    "high_recall": {
        "strategy": "recall_priority",
        "recall_floor": 0.90,
        "precision_floor": 0.60,
        "beta": 2.0,
        "threshold_min": 0.20,
        "threshold_max": 0.80,
        "threshold_step": 0.01,
        "best_model_metric": "fbeta",
    },
    "high_precision": {
        "strategy": "precision_priority",
        "recall_floor": 0.60,
        "precision_floor": 0.80,
        "beta": 1.0,
        "threshold_min": 0.20,
        "threshold_max": 0.80,
        "threshold_step": 0.01,
        "best_model_metric": "precision",
    },
    "best_roc_auc": {
        "strategy": "balanced_f1_with_recall_floor",
        "recall_floor": 0.75,
        "precision_floor": 0.65,
        "beta": 1.0,
        "threshold_min": 0.20,
        "threshold_max": 0.80,
        "threshold_step": 0.01,
        "best_model_metric": "roc_auc",
    },
    "best_pr_auc": {
        "strategy": "balanced_f1_with_recall_floor",
        "recall_floor": 0.75,
        "precision_floor": 0.65,
        "beta": 1.0,
        "threshold_min": 0.20,
        "threshold_max": 0.80,
        "threshold_step": 0.01,
        "best_model_metric": "pr_auc",
    },
    "custom": {
        "strategy": "custom",
        "recall_floor": 0.80,
        "precision_floor": 0.70,
        "beta": 1.0,
        "threshold_min": 0.20,
        "threshold_max": 0.80,
        "threshold_step": 0.01,
        "best_model_metric": "f1",
    },
}


@dataclass(frozen=True)
class ThresholdTuningConfig:
    strategy: str = "balanced_f1_with_recall_floor"
    recall_floor: float = 0.80
    precision_floor: float = 0.70
    beta: float = 1.3
    threshold_min: float = 0.20
    threshold_max: float = 0.80
    threshold_step: float = 0.01
    best_model_metric: str = "f1"


def resolve_profile_config(profile: str | None, overrides: dict[str, Any] | None = None) -> ThresholdTuningConfig:
    profile_key = profile or "balanced_production"
    if profile_key not in PROFILE_DEFAULTS:
        raise ValueError(f"Unsupported training_profile: {profile_key}")
    values = dict(PROFILE_DEFAULTS[profile_key])
    if profile_key == "custom" and overrides:
        values.update({key: value for key, value in overrides.items() if value is not None})
    elif overrides and overrides.get("strategy"):
        values["strategy"] = overrides["strategy"]

    if values["strategy"] not in THRESHOLD_STRATEGIES:
        raise ValueError(f"Unsupported threshold strategy: {values['strategy']}")
    if not 0.0 <= float(values["recall_floor"]) <= 1.0:
        raise ValueError("recall_floor must be in [0,1]")
    if not 0.0 <= float(values["precision_floor"]) <= 1.0:
        raise ValueError("precision_floor must be in [0,1]")
    if not 0.2 <= float(values["threshold_min"]) <= float(values["threshold_max"]) <= 0.8:
        raise ValueError("threshold range must satisfy 0.20 <= min <= max <= 0.80")
    if float(values["threshold_step"]) <= 0 or float(values["threshold_step"]) > 0.2:
        raise ValueError("threshold_step must be in (0, 0.2]")
    if float(values["beta"]) <= 0:
        raise ValueError("beta must be positive")
    return ThresholdTuningConfig(**values)


def _cm_dict(y_true, y_pred) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).astype(int).ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def metrics_at_threshold(y_true, y_proba, threshold: float, beta: float = 1.0) -> dict:
    probabilities = np.asarray(y_proba, dtype=float)
    y_pred = (probabilities >= float(threshold)).astype(int)
    cm = _cm_dict(y_true, y_pred)
    tn, fp, fn, tp = cm["tn"], cm["fp"], cm["fn"], cm["tp"]
    total = tn + fp + fn + tp
    negative_total = tn + fp
    positive_total = fn + tp
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    fbeta = float(fbeta_score(y_true, y_pred, beta=beta, zero_division=0))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "f1_score": f1,
        "fbeta": fbeta,
        "fbeta_score": fbeta,
        "fbeta_beta": float(beta),
        "false_positive_count": int(fp),
        "false_negative_count": int(fn),
        "false_positive_rate": float(fp / negative_total) if negative_total else 0.0,
        "false_negative_rate": float(fn / positive_total) if positive_total else 0.0,
        "predicted_positive_rate": float((tp + fp) / total) if total else 0.0,
        "predicted_negative_rate": float((tn + fn) / total) if total else 0.0,
        "confusion_matrix": cm,
        "threshold": float(round(threshold, 4)),
    }


def _threshold_grid(config: ThresholdTuningConfig) -> list[float]:
    values = np.arange(config.threshold_min, config.threshold_max + config.threshold_step / 2, config.threshold_step)
    return [float(round(value, 4)) for value in values]


def _sort_by_f1(item: dict) -> tuple:
    return (
        float(item.get("f1_score") or 0.0),
        float(item.get("precision") or 0.0),
        float(item.get("recall") or 0.0),
        -float(item.get("false_positive_rate") or 0.0),
    )


def _sort_by_fbeta(item: dict) -> tuple:
    return (
        float(item.get("fbeta_score") or 0.0),
        float(item.get("recall") or 0.0),
        float(item.get("precision") or 0.0),
        -float(item.get("false_negative_count") or 0.0),
    )


def _sort_by_precision(item: dict) -> tuple:
    return (
        float(item.get("precision") or 0.0),
        float(item.get("f1_score") or 0.0),
        float(item.get("recall") or 0.0),
        -float(item.get("false_positive_count") or 0.0),
    )


def _sort_custom(item: dict, metric: str) -> tuple:
    if metric == "fbeta":
        return _sort_by_fbeta(item)
    if metric == "precision_weighted":
        score = 0.65 * float(item.get("precision") or 0.0) + 0.35 * float(item.get("recall") or 0.0)
        return (score, float(item.get("f1_score") or 0.0), -float(item.get("false_positive_rate") or 0.0))
    if metric == "recall_weighted":
        score = 0.65 * float(item.get("recall") or 0.0) + 0.35 * float(item.get("precision") or 0.0)
        return (score, float(item.get("f1_score") or 0.0), -float(item.get("false_negative_rate") or 0.0))
    if metric == "balanced_score":
        balance = min(float(item.get("precision") or 0.0), float(item.get("recall") or 0.0))
        return (balance, float(item.get("f1_score") or 0.0), -float(item.get("false_positive_rate") or 0.0))
    return _sort_by_f1(item)


def _top_candidates(candidates: list[dict], config: ThresholdTuningConfig) -> list[dict]:
    recall_pool = [item for item in candidates if item["recall"] >= config.recall_floor] or candidates
    precision_pool = [item for item in recall_pool if item["precision"] >= min(config.precision_floor, 0.65)]
    pool = precision_pool or recall_pool
    return sorted(pool, key=lambda item: _sort_custom(item, config.best_model_metric), reverse=True)[:5]


def tune_threshold(y_true, y_proba, config: ThresholdTuningConfig | dict[str, Any]) -> dict:
    if isinstance(config, dict):
        config = ThresholdTuningConfig(**config)
    candidates = [metrics_at_threshold(y_true, y_proba, threshold, config.beta) for threshold in _threshold_grid(config)]
    if not candidates:
        selected = metrics_at_threshold(y_true, y_proba, 0.5, config.beta)
        return {
            "strategy": config.strategy,
            "config": asdict(config),
            "selected": selected,
            "selected_threshold": selected["threshold"],
            "threshold_metrics": selected,
            "threshold_candidates_top_5": [selected],
            "reason_for_selection": "No threshold candidates were generated; default threshold was used.",
            "candidates": [selected],
        }

    reason = ""
    if config.strategy == "balanced_f1_with_recall_floor":
        recall_pool = [item for item in candidates if item["recall"] >= config.recall_floor]
        precision_pool = [item for item in recall_pool if item["precision"] >= config.precision_floor]
        if precision_pool:
            selected = max(precision_pool, key=_sort_by_f1)
            reason = f"Selected highest-F1 threshold with recall >= {config.recall_floor:.2f} and precision >= {config.precision_floor:.2f}."
        elif recall_pool:
            selected = max(recall_pool, key=_sort_by_f1)
            reason = f"No threshold met precision floor {config.precision_floor:.2f}; selected highest-F1 threshold meeting recall floor."
            logger.warning(reason)
        else:
            selected = max(candidates, key=_sort_by_f1)
            reason = f"No threshold met recall floor {config.recall_floor:.2f}; selected global highest-F1 threshold."
            logger.warning(reason)
    elif config.strategy == "recall_priority":
        recall_pool = [item for item in candidates if item["recall"] >= config.recall_floor]
        precision_guard = [item for item in recall_pool if item["precision"] >= config.precision_floor]
        selected = max(precision_guard or recall_pool or candidates, key=_sort_by_fbeta)
        reason = f"Selected threshold by F-beta beta={config.beta:.2f} with recall priority."
        if selected["false_positive_rate"] > 0.55:
            logger.warning("Recall-priority threshold has high false-positive rate %.3f", selected["false_positive_rate"])
    elif config.strategy == "precision_priority":
        precision_pool = [item for item in candidates if item["precision"] >= config.precision_floor]
        recall_guard = [item for item in precision_pool if item["recall"] >= config.recall_floor]
        selected = max(recall_guard or precision_pool or candidates, key=_sort_by_precision)
        reason = f"Selected threshold by precision floor {config.precision_floor:.2f}, then F1/recall."
        if selected["recall"] < config.recall_floor:
            logger.warning("Precision-priority threshold has recall %.3f below floor %.3f", selected["recall"], config.recall_floor)
    elif config.strategy == "custom":
        selected = max(candidates, key=lambda item: _sort_custom(item, config.best_model_metric))
        reason = f"Selected threshold by custom metric: {config.best_model_metric}."
    else:
        selected = max(candidates, key=_sort_by_f1)
        reason = "Selected threshold with highest F1 score."

    return {
        "strategy": config.strategy,
        "config": asdict(config),
        "selected": selected,
        "selected_threshold": selected["threshold"],
        "threshold_metrics": selected,
        "threshold_candidates_top_5": _top_candidates(candidates, config),
        "reason_for_selection": reason,
        "baseline": metrics_at_threshold(y_true, y_proba, 0.5, config.beta),
        "candidates": candidates,
    }


def profile_metadata() -> list[dict]:
    labels = {
        "balanced_production": "Balanced Production",
        "high_recall": "High Recall",
        "high_precision": "High Precision",
        "best_roc_auc": "Best ROC-AUC",
        "best_pr_auc": "Best PR-AUC",
        "custom": "Custom",
    }
    descriptions = {
        "balanced_production": "Balances precision and recall for production alert quality.",
        "high_recall": "Prioritizes fewer missed defects; may increase false positives.",
        "high_precision": "Prioritizes lower alert noise; may miss more defects.",
        "best_roc_auc": "Ranks models by class separability using ROC-AUC.",
        "best_pr_auc": "Ranks models by average precision for imbalanced data.",
        "custom": "Uses user-provided threshold and ranking settings.",
    }
    return [
        {"key": key, "label": labels[key], "description": descriptions[key], "config": value}
        for key, value in PROFILE_DEFAULTS.items()
    ]

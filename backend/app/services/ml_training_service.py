from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.feature_contract import (
    ENGINEERED_OUTPUT_COLUMNS,
    EXCLUDED_LEAKAGE_COLUMNS,
    SAFE_MODEL_FEATURE_COLUMNS,
    MODEL_FEATURE_SCHEMA_VERSION,
    assert_safe_model_features,
)
from app.ml.feature_engineering import build_p7_features
from app.ml.threshold_tuning import (
    ThresholdTuningConfig,
    metrics_at_threshold as threshold_metrics_at,
    profile_metadata,
    resolve_profile_config,
    tune_threshold,
)
from app.repositories import metric_repository, model_repository
from app.schemas.model_schema import TrainingRequest
from app.services.audit_service import log_action

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
PRODUCTION_ARTIFACT = ARTIFACT_DIR / "defectai_p7_production.joblib"
PRODUCTION_METADATA = ARTIFACT_DIR / "defectai_p7_production_metadata.json"
DEFAULT_THRESHOLD = 0.5
BALANCED_THRESHOLD_STRATEGY = "balanced_f1_with_recall_floor"
BALANCED_BETA = 1.3
TARGET_PRECISION = 0.70
MIN_ACCEPTABLE_PRECISION = 0.65
MAX_FALSE_POSITIVE_RATE = 0.55
MAX_PREDICTED_POSITIVE_RATE = 0.75
MIN_TRAINING_RECORDS = 4
SMALL_DATASET_WARNING_THRESHOLD = 20
MLP_EARLY_STOPPING_MIN_ROWS = 50
logger = logging.getLogger(__name__)

MODEL_NAMES = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "neural_network": "Neural Network",
}


def _estimator(model_type: str, payload: TrainingRequest, training_rows: int | None = None):
    hyperparams = (payload.model_hyperparams or {}).get(model_type, {})
    if model_type == "logistic_regression":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=max(payload.max_iter, 1000),
                        class_weight=hyperparams.get("class_weight", "balanced"),
                        solver=hyperparams.get("solver", "lbfgs"),
                        C=float(hyperparams.get("C", 1.0)),
                        random_state=payload.random_state,
                    ),
                ),
            ]
        )
    if model_type == "random_forest":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=int(hyperparams.get("n_estimators", 300)),
                        max_depth=hyperparams.get("max_depth"),
                        min_samples_leaf=int(hyperparams.get("min_samples_leaf", 1)),
                        class_weight=hyperparams.get("class_weight", "balanced_subsample"),
                        random_state=payload.random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
    if model_type == "neural_network":
        hidden = int(payload.hidden_layer_size)
        hidden_layers = hyperparams.get("hidden_layer_sizes", (hidden, max(8, hidden // 2)))
        if isinstance(hidden_layers, list):
            hidden_layers = tuple(int(value) for value in hidden_layers)
        early_stopping = training_rows is None or training_rows >= MLP_EARLY_STOPPING_MIN_ROWS
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    MLPClassifier(
                        hidden_layer_sizes=hidden_layers,
                        activation=hyperparams.get("activation", "relu"),
                        solver=hyperparams.get("solver", "adam"),
                        alpha=float(hyperparams.get("alpha", 0.0001)),
                        learning_rate_init=float(hyperparams.get("learning_rate_init", 0.001)),
                        max_iter=max(payload.max_iter, 1000),
                        early_stopping=bool(hyperparams.get("early_stopping", early_stopping)),
                        validation_fraction=float(hyperparams.get("validation_fraction", 0.15)),
                        n_iter_no_change=20,
                        random_state=payload.random_state,
                    ),
                ),
            ]
        )
    raise ValueError(f"Unsupported model: {model_type}")


def _types(payload: TrainingRequest):
    if payload.selected_models:
        return payload.selected_models
    if payload.model_types:
        return payload.model_types
    if payload.model_type and payload.model_type != "all":
        return [payload.model_type]
    return ["logistic_regression", "random_forest", "neural_network"]


def _safe_metric(metric_name: str, y_true, probabilities) -> float | None:
    if pd.Series(y_true).nunique() != 2:
        logger.warning("%s skipped: test set contains a single class", metric_name)
        return None
    try:
        if metric_name == "roc_auc":
            return float(roc_auc_score(y_true, probabilities))
        if metric_name == "pr_auc":
            return float(average_precision_score(y_true, probabilities))
    except Exception as exc:
        logger.warning("%s skipped: %s", metric_name, exc)
    return None


def _cm_dict(y_true, y_pred) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).astype(int).ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def _metrics_at_threshold(y_true, probabilities, threshold: float) -> dict:
    return threshold_metrics_at(y_true, probabilities, threshold, beta=BALANCED_BETA)


def _classification_metrics(y_true, probabilities, threshold: float, beta: float = BALANCED_BETA) -> dict:
    metrics = threshold_metrics_at(y_true, probabilities, threshold, beta=beta)
    metrics["roc_auc"] = _safe_metric("roc_auc", y_true, probabilities)
    metrics["pr_auc"] = _safe_metric("pr_auc", y_true, probabilities)
    return metrics


def _candidate_sort_key(item: dict) -> tuple:
    return (
        float(item.get("f1_score") or 0.0),
        float(item.get("precision") or 0.0),
        float(item.get("recall") or 0.0),
        -float(item.get("false_positive_rate") or 0.0),
        -float(item.get("predicted_positive_rate") or 0.0),
    )


def _top_threshold_candidates(candidates: list[dict], target_recall: float, limit: int = 5) -> list[dict]:
    recall_floor = [item for item in candidates if item["recall"] >= target_recall]
    pool = recall_floor or candidates
    preferred = [item for item in pool if item["precision"] >= MIN_ACCEPTABLE_PRECISION]
    return sorted(preferred or pool, key=_candidate_sort_key, reverse=True)[:limit]


def _tune_threshold(y_true, probabilities, strategy: str, target_recall: float) -> dict:
    resolved = ThresholdTuningConfig(
        strategy="balanced_f1_with_recall_floor" if strategy in {"recall_weighted", "min_recall"} else strategy,
        recall_floor=target_recall,
        precision_floor=TARGET_PRECISION,
        beta=BALANCED_BETA,
        threshold_min=0.20,
        threshold_max=0.80,
        threshold_step=0.01,
        best_model_metric="f1",
    )
    return tune_threshold(y_true, probabilities, resolved)


def _evaluate_estimator(estimator, X_test, y_test, threshold: float, beta: float = BALANCED_BETA):
    probabilities = np.clip(estimator.predict_proba(X_test)[:, 1].astype(float), 0.0, 1.0)
    y_pred = (probabilities >= threshold).astype(int)
    return y_pred, probabilities, _classification_metrics(y_test, probabilities, threshold, beta=beta)


def _cross_validation_metrics(model_type: str, X: pd.DataFrame, y: pd.Series, payload: TrainingRequest) -> dict:
    min_class_count = int(y.value_counts().min()) if y.nunique() == 2 else 0
    n_splits = min(5, min_class_count)
    if n_splits < 2:
        return {"enabled": False, "reason": "not enough samples per class"}
    estimator = _estimator(model_type, payload, training_rows=len(X))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=payload.random_state)
    scoring = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "pr_auc": "average_precision",
    }
    try:
        scores = cross_validate(estimator, X, y, scoring=scoring, cv=cv, n_jobs=None, error_score=np.nan)
    except Exception as exc:
        logger.exception("Cross-validation failed for %s", model_type)
        return {"enabled": False, "reason": str(exc)}
    result = {"enabled": True, "folds": n_splits}
    for metric_name in scoring:
        values = np.asarray(scores.get(f"test_{metric_name}", []), dtype=float)
        result[f"{metric_name}_mean"] = float(np.nanmean(values)) if values.size else None
        result[f"{metric_name}_std"] = float(np.nanstd(values)) if values.size else None
    return result


def _feature_importance(estimator, X_test: pd.DataFrame, y_test: pd.Series, payload: TrainingRequest) -> dict:
    model = estimator.named_steps.get("model") if hasattr(estimator, "named_steps") else estimator
    result: dict = {"feature_importance": [], "permutation_importance": []}
    if hasattr(model, "feature_importances_"):
        result["feature_importance"] = [
            {"feature": feature, "importance": float(importance)}
            for feature, importance in sorted(
                zip(SAFE_MODEL_FEATURE_COLUMNS, model.feature_importances_),
                key=lambda item: float(item[1]),
                reverse=True,
            )
        ]
    if len(X_test) >= 4 and y_test.nunique() == 2:
        try:
            perm = permutation_importance(
                estimator,
                X_test,
                y_test,
                n_repeats=5,
                random_state=payload.random_state,
                scoring="average_precision",
            )
            result["permutation_importance"] = [
                {"feature": feature, "importance_mean": float(mean), "importance_std": float(std)}
                for feature, mean, std in sorted(
                    zip(SAFE_MODEL_FEATURE_COLUMNS, perm.importances_mean, perm.importances_std),
                    key=lambda item: float(item[1]),
                    reverse=True,
                )
            ]
        except Exception as exc:
            logger.warning("Permutation importance skipped: %s", exc)
            result["permutation_importance_error"] = str(exc)
    return result


def _prepare_training_frame(payload: TrainingRequest):
    assert_safe_model_features(SAFE_MODEL_FEATURE_COLUMNS)
    rows = metric_repository.training_records(payload.project_id, payload.dataset_id)
    if len(rows) < MIN_TRAINING_RECORDS:
        raise ValueError(
            f"Dataset has only {len(rows)} labeled records. "
            f"At least {MIN_TRAINING_RECORDS} labeled rows are required, with at least 2 rows in each label class."
        )

    df = build_p7_features(pd.DataFrame(rows), use_label_density=False, use_defect_count_density=False)
    if "defect_label" not in df.columns:
        raise ValueError("Training requires defect_label with values 0 (No Defect) or 1 (Defect).")

    labels = pd.to_numeric(df["defect_label"], errors="coerce")
    if labels.isna().any() or not labels.dropna().isin([0, 1]).all():
        raise ValueError("defect_label must contain only 0 or 1 for every training row.")
    df["defect_label"] = labels.astype(int)

    label_counts = df["defect_label"].value_counts()
    if df["defect_label"].nunique() < 2:
        raise ValueError(
            f"Dataset has only one label class ({df['defect_label'].iloc[0]}). "
            "Training requires both defect_label=0 and defect_label=1."
        )
    if int(label_counts.min()) < 2:
        raise ValueError("Training requires at least 2 records for each label class so stratified train/test split can run.")

    unsafe_present = [column for column in EXCLUDED_LEAKAGE_COLUMNS if column in SAFE_MODEL_FEATURE_COLUMNS]
    if unsafe_present:
        raise ValueError(f"Leakage columns present in SAFE_MODEL_FEATURE_COLUMNS: {unsafe_present}")

    X = df.reindex(columns=SAFE_MODEL_FEATURE_COLUMNS).apply(pd.to_numeric, errors="coerce")
    if list(X.columns) != SAFE_MODEL_FEATURE_COLUMNS:
        raise ValueError("Training feature order mismatch.")
    y = df["defect_label"].astype(int)
    stratify = y if y.nunique() == 2 and y.value_counts().min() >= 2 else None
    warnings = list(df.attrs.get("warnings", []))
    if len(df) < SMALL_DATASET_WARNING_THRESHOLD:
        warnings.append(f"Small training dataset: {len(df)} labeled rows. Collect more data before production use.")

    split_test_size = payload.test_size
    minimum_stratified_test_size = 2 / len(y)
    if stratify is not None and split_test_size < minimum_stratified_test_size:
        split_test_size = min(0.5, minimum_stratified_test_size)
        warnings.append(f"Adjusted test_size from {payload.test_size} to {round(split_test_size, 4)} so the stratified test split contains both classes.")

    split = train_test_split(X, y, test_size=split_test_size, random_state=payload.random_state, stratify=stratify)
    dataset_profile = {
        "row_count": int(len(df)),
        "class_distribution": {str(k): int(v) for k, v in label_counts.to_dict().items()},
        "feature_warnings": warnings,
        "requested_test_size": payload.test_size,
        "effective_test_size": split_test_size,
        "excluded_leakage_columns": EXCLUDED_LEAKAGE_COLUMNS,
        "engineered_output_columns": ENGINEERED_OUTPUT_COLUMNS,
        "safe_model_feature_columns": SAFE_MODEL_FEATURE_COLUMNS,
    }
    return (*split, dataset_profile)


def _selection_score(item: dict, metric: str) -> float:
    if metric in {"roc_auc", "pr_auc", "precision", "recall"}:
        return float(item.get(metric) or 0.0)
    if metric == "fbeta":
        return float(item.get("fbeta_score") or 0.0)
    if metric == "balanced_score":
        return min(float(item.get("precision") or 0.0), float(item.get("recall") or 0.0))
    return float(item.get("f1_score") or 0.0)


def _select_best_model(trained: list[dict], metric: str) -> dict:
    if metric == "roc_auc":
        return max(
            trained,
            key=lambda item: (
                float(item.get("roc_auc") or -1.0),
                float(item.get("pr_auc") or -1.0),
                float(item.get("f1_score") or 0.0),
                min(float(item.get("precision") or 0.0), float(item.get("recall") or 0.0)),
                -abs(float(item.get("overfit_gap") or 0.0)),
            ),
        )
    if metric == "pr_auc":
        return max(
            trained,
            key=lambda item: (
                float(item.get("pr_auc") or -1.0),
                float(item.get("f1_score") or 0.0),
                float(item.get("recall") or 0.0),
                float(item.get("precision") or 0.0),
                -abs(float(item.get("overfit_gap") or 0.0)),
            ),
        )
    if metric == "fbeta":
        return max(
            trained,
            key=lambda item: (
                float(item.get("fbeta_score") or 0.0),
                float(item.get("f1_score") or 0.0),
                float(item.get("pr_auc") or -1.0),
                float(item.get("precision") or 0.0),
                -float(item.get("false_negative_count") or 999999.0),
            ),
        )
    if metric == "precision":
        return max(
            trained,
            key=lambda item: (
                float(item.get("precision") or 0.0),
                float(item.get("f1_score") or 0.0),
                float(item.get("pr_auc") or -1.0),
                float(item.get("roc_auc") or -1.0),
                -float(item.get("false_positive_count") or 999999.0),
            ),
        )
    if metric in {"f1", "balanced_score"}:
        return max(
            trained,
            key=lambda item: (
                float(item.get("f1_score") or 0.0),
                min(float(item.get("precision") or 0.0), float(item.get("recall") or 0.0)),
                float(item.get("precision") or 0.0),
                float(item.get("recall") or 0.0),
                float(item.get("pr_auc") or -1.0),
                float(item.get("roc_auc") or -1.0),
                -float(item.get("latency_ms") or 999999.0),
            ),
        )
    return max(trained, key=lambda item: (float(item.get("f1_score") or 0.0), float(item.get("pr_auc") or -1.0)))


def train(payload: TrainingRequest):
    return train_production(payload, model_types=_types(payload))


def _threshold_config_from_payload(payload: TrainingRequest) -> ThresholdTuningConfig:
    overrides = payload.threshold_config.model_dump(exclude_none=True) if payload.threshold_config else {}
    if payload.threshold_strategy:
        strategy = payload.threshold_strategy
        if strategy == "recall_weighted":
            strategy = "recall_priority"
        elif strategy == "min_recall":
            strategy = "balanced_f1_with_recall_floor"
        overrides["strategy"] = strategy
        overrides.setdefault("recall_floor", payload.target_recall)
    return resolve_profile_config(payload.training_profile, overrides)


def _artifact_paths(version: str, model_type: str, profile: str) -> tuple[Path, Path]:
    stem = f"defectai_p7_{profile}_{model_type}_{version}"
    return ARTIFACT_DIR / f"{stem}.joblib", ARTIFACT_DIR / f"{stem}_metadata.json"


def _metrics_subset(item: dict) -> dict:
    keys = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "f1_score",
        "fbeta",
        "fbeta_score",
        "fbeta_beta",
        "roc_auc",
        "pr_auc",
        "false_positive_count",
        "false_negative_count",
        "false_positive_rate",
        "false_negative_rate",
        "predicted_positive_rate",
        "confusion_matrix",
    ]
    return {key: item.get(key) for key in keys}


def train_production(payload: TrainingRequest, model_types: list[str] | None = None):
    threshold_config = _threshold_config_from_payload(payload)
    selected_models = list(model_types or _types(payload))
    X_train, X_test, y_train, y_test, dataset_profile = _prepare_training_frame(payload)
    X_all = pd.concat([X_train, X_test], axis=0)
    y_all = pd.concat([y_train, y_test], axis=0)

    trained: list[dict] = []
    failed: list[dict] = []
    version = datetime.now().strftime("v%Y%m%d%H%M%S%f")
    created_at = datetime.now().isoformat()
    fitted_estimators = {}
    warning_messages = list(dataset_profile.get("feature_warnings", []))

    for model_type in selected_models:
        try:
            estimator = _estimator(model_type, payload, training_rows=len(X_train))
            start = time.perf_counter()
            estimator.fit(X_train, y_train)
            training_seconds = time.perf_counter() - start

            probabilities = np.clip(estimator.predict_proba(X_test)[:, 1].astype(float), 0.0, 1.0)
            tuning = tune_threshold(y_test, probabilities, threshold_config)
            threshold = float(tuning["selected"]["threshold"])
            selected_threshold_metrics = tuning["selected"]
            if selected_threshold_metrics.get("precision", 0.0) < threshold_config.precision_floor:
                warning_messages.append(
                    f"{MODEL_NAMES[model_type]} selected threshold {threshold:.2f} has precision "
                    f"{selected_threshold_metrics.get('precision', 0.0):.3f}, below production guardrail "
                    f"{threshold_config.precision_floor:.2f}."
                )
            if selected_threshold_metrics.get("false_positive_rate", 0.0) > MAX_FALSE_POSITIVE_RATE:
                warning_messages.append(
                    f"{MODEL_NAMES[model_type]} selected threshold {threshold:.2f} has false-positive rate "
                    f"{selected_threshold_metrics.get('false_positive_rate', 0.0):.3f}; review warning volume."
                )

            train_pred, train_probabilities, train_metrics = _evaluate_estimator(estimator, X_train, y_train, threshold, threshold_config.beta)
            pred_start = time.perf_counter()
            y_pred, probabilities, metrics = _evaluate_estimator(estimator, X_test, y_test, threshold, threshold_config.beta)
            latency_ms = ((time.perf_counter() - pred_start) / max(len(X_test), 1)) * 1000
            cv_metrics = _cross_validation_metrics(model_type, X_all, y_all, payload)
            importance = _feature_importance(estimator, X_test, y_test, payload) if model_type == "random_forest" else {}
            train_auc = train_metrics.get("roc_auc") or 0.0
            test_auc = metrics.get("roc_auc") or 0.0
            overfit_gap = round(float(train_auc - test_auc), 4)
            if overfit_gap > 0.15:
                warning_messages.append(f"{MODEL_NAMES[model_type]} may be overfitting: train ROC-AUC exceeds test ROC-AUC by {overfit_gap}.")

            metrics.update(
                {
                    "threshold": threshold,
                    "threshold_strategy": threshold_config.strategy,
                    "selected_threshold": threshold,
                    "threshold_metrics": tuning["selected"],
                    "threshold_candidates_top_5": tuning.get("threshold_candidates_top_5", []),
                    "reason_for_selection": tuning.get("reason_for_selection"),
                    "threshold_tuning": {
                        "strategy": tuning["strategy"],
                        "baseline": tuning.get("baseline"),
                        "selected": tuning["selected"],
                        "threshold_candidates_top_5": tuning.get("threshold_candidates_top_5", []),
                        "reason_for_selection": tuning.get("reason_for_selection"),
                    },
                }
            )
            fitted_estimators[model_type] = {
                "estimator": estimator,
                "latency_ms": round(latency_ms, 4),
                "training_time_seconds": round(training_seconds, 4),
                "y_pred": y_pred,
                "train_y_pred": train_pred,
                "metrics": metrics,
                "train_metrics": train_metrics,
                "cross_validation": cv_metrics,
                "overfit_gap": overfit_gap,
                **importance,
            }
            trained.append(
                {
                    "model_type": model_type,
                    "model_key": model_type,
                    "model_name": MODEL_NAMES[model_type],
                    "training_profile": payload.training_profile,
                    "status": "success",
                    "latency_ms": round(latency_ms, 4),
                    "prediction_latency_ms": round(latency_ms, 4),
                    "training_time_seconds": round(training_seconds, 4),
                    "train_time_seconds": round(training_seconds, 4),
                    "train_score": train_metrics.get("roc_auc"),
                    "test_score": metrics.get("roc_auc"),
                    "train_metrics": train_metrics,
                    "cross_validation": cv_metrics,
                    "overfit_gap": overfit_gap,
                    **importance,
                    **metrics,
                }
            )
        except Exception as exc:
            logger.exception("Training failed for %s", model_type)
            failed.append({"model_type": model_type, "model_name": MODEL_NAMES.get(model_type, model_type), "error": str(exc)})

    if not trained:
        raise ValueError(f"All model training attempts failed: {failed}")

    selection_metric = payload.best_model_strategy or threshold_config.best_model_metric
    if selection_metric in {"balanced_f1_with_recall_floor", "best_f1"}:
        selection_metric = "f1"
    if selection_metric in {"recall_priority", "recall_weighted"}:
        selection_metric = "fbeta"
    if selection_metric == "precision_priority":
        selection_metric = "precision"
    if selection_metric == "best_roc_auc":
        selection_metric = "roc_auc"
    if selection_metric == "best_pr_auc":
        selection_metric = "pr_auc"
    best = _select_best_model(trained, selection_metric)
    best_fit = fitted_estimators[best["model_type"]]
    selection_score = _selection_score(best, selection_metric)
    selection_reason = (
        f"Selected {best['model_name']} using {payload.training_profile}/{selection_metric}; "
        f"score={selection_score:.4f}, f1={best['f1_score']:.4f}, precision={best['precision']:.4f}, "
        f"recall={best['recall']:.4f}, pr_auc={best.get('pr_auc')}, threshold={best['threshold']:.2f}."
    )

    if any(round(float(item["accuracy"]), 6) >= 1.0 for item in trained):
        warning_messages.append("Perfect accuracy detected. Dataset may be too small, duplicated, or too easy. Validate with another dataset.")

    common_metadata = {
        "artifact_schema_version": 2,
        "version": version,
        "best_model_type": best["model_type"],
        "best_model_name": best["model_name"],
        "best_model_key": best["model_type"],
        "feature_schema_version": MODEL_FEATURE_SCHEMA_VERSION,
        "feature_columns": SAFE_MODEL_FEATURE_COLUMNS,
        "engineered_output_columns": ENGINEERED_OUTPUT_COLUMNS,
        "excluded_leakage_columns": EXCLUDED_LEAKAGE_COLUMNS,
        "training_profile": payload.training_profile,
        "threshold_config": threshold_config.__dict__,
        "selection_strategy": payload.training_profile,
        "selection_metric": selection_metric,
        "selection_score": selection_score,
        "selection_reason": selection_reason,
        "auto_activated": bool(payload.auto_activate_best),
        "comparison": trained,
        "failed_models": failed,
        "warnings": warning_messages,
        "dataset_id": payload.dataset_id,
        "dataset_profile": dataset_profile,
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "requested_test_size_ratio": payload.test_size,
        "test_size_ratio": dataset_profile.get("effective_test_size", payload.test_size),
        "random_state": payload.random_state,
        "sklearn_version": sklearn.__version__,
        "created_at": created_at,
    }

    run_map = []
    best_model_id = None
    ordered_trained = sorted(trained, key=lambda item: 0 if item["model_type"] == best["model_type"] else 1)
    for item in ordered_trained:
        item_selection_score = _selection_score(item, selection_metric)
        is_best = item["model_type"] == best["model_type"]
        artifact_path, metadata_path = _artifact_paths(version, item["model_type"], payload.training_profile)
        item_metadata = {
            **common_metadata,
            "name": f"DefectAI P7 {item['model_name']}",
            "model_type": item["model_type"],
            "model_key": item["model_type"],
            "model_name": item["model_name"],
            "metrics": _metrics_subset(item),
            "threshold": item["threshold"],
            "selected_threshold": item["threshold"],
            "threshold_strategy": item["threshold_strategy"],
            "threshold_metrics": item.get("threshold_metrics"),
            "threshold_candidates_top_5": item.get("threshold_candidates_top_5", []),
            "threshold_tuning": item.get("threshold_tuning"),
            "selection_score": item_selection_score,
            "is_best": is_best,
            "reason_for_selection": item.get("reason_for_selection") or selection_reason,
        }
        artifact_payload = {
            "estimator": fitted_estimators[item["model_type"]]["estimator"],
            "feature_columns": SAFE_MODEL_FEATURE_COLUMNS,
            "metadata": item_metadata,
        }
        joblib.dump(artifact_payload, artifact_path)
        metadata_path.write_text(json.dumps(item_metadata, indent=2), encoding="utf-8")
        model_id = model_repository.create_model(
            {
                "name": item_metadata["name"],
                "model_type": item["model_type"],
                "version": version,
                "artifact_path": str(artifact_path),
                "metadata_path": str(metadata_path),
                "is_active": 0,
                "is_best": is_best,
                "dataset_id": payload.dataset_id,
                "training_profile": payload.training_profile,
                "latency_ms": item["latency_ms"],
                "hyperparameters_json": json.dumps(
                    {
                        **payload.model_dump(),
                        "threshold_config": threshold_config.__dict__,
                        "threshold": item["threshold"],
                        "selection_strategy": payload.training_profile,
                        "selection_metric": selection_metric,
                        "selection_score": item_selection_score,
                        "selection_reason": selection_reason,
                        "sklearn_version": sklearn.__version__,
                        "excluded_leakage_columns": EXCLUDED_LEAKAGE_COLUMNS,
                    },
                    ensure_ascii=False,
                ),
                "feature_list_json": json.dumps(SAFE_MODEL_FEATURE_COLUMNS),
                "metrics_json": json.dumps(_metrics_subset(item), ensure_ascii=False),
                "pr_auc": item.get("pr_auc"),
                "threshold": item["threshold"],
                "selection_strategy": payload.training_profile,
                "selection_metric": selection_metric,
                "selection_score": item_selection_score,
                "status": "success",
                **{key: item.get(key) for key in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]},
            }
        )
        item["model_id"] = model_id
        item["artifact_path"] = str(artifact_path)
        item["metadata_path"] = str(metadata_path)
        item["selection_score"] = item_selection_score
        item["is_best"] = is_best
        if is_best:
            best_model_id = model_id
            model_repository.mark_best_model(model_id)
            joblib.dump(artifact_payload, PRODUCTION_ARTIFACT)
            PRODUCTION_METADATA.write_text(json.dumps(item_metadata, indent=2), encoding="utf-8")

        run_id = model_repository.create_training_run(
            {
                "model_id": model_id,
                "dataset_id": payload.dataset_id,
                "model_type": item["model_type"],
                "model_version": version,
                "status": "completed",
                "train_size": len(X_train),
                "test_size": len(X_test),
                "confusion_matrix_json": json.dumps(item["confusion_matrix"]),
                "training_time_seconds": item["training_time_seconds"],
                "pr_auc": item.get("pr_auc"),
                "threshold": item["threshold"],
                "selection_strategy": payload.training_profile,
                "selection_metric": selection_metric,
                "selection_score": item_selection_score,
                "parameters_json": json.dumps(
                    {
                        "feature_columns": SAFE_MODEL_FEATURE_COLUMNS,
                        **payload.model_dump(),
                        "warnings": warning_messages,
                        "threshold": item["threshold"],
                        "selected_threshold": item["threshold"],
                        "threshold_config": threshold_config.__dict__,
                        "threshold_metrics": item.get("threshold_metrics"),
                        "threshold_candidates_top_5": item.get("threshold_candidates_top_5"),
                        "reason_for_selection": item.get("reason_for_selection"),
                        "threshold_tuning": item.get("threshold_tuning"),
                        "cross_validation": item.get("cross_validation"),
                        "train_metrics": item.get("train_metrics"),
                        "overfit_gap": item.get("overfit_gap"),
                        "excluded_leakage_columns": EXCLUDED_LEAKAGE_COLUMNS,
                    },
                    ensure_ascii=False,
                ),
                "selected_models_json": json.dumps(selected_models),
                "training_profile": payload.training_profile,
                "threshold_config_json": json.dumps(threshold_config.__dict__),
                "best_model_id": best_model_id,
                "results_json": json.dumps(trained, default=str, ensure_ascii=False),
                "started_at": datetime.now(),
                "completed_at": datetime.now(),
                **{key: item.get(key) for key in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]},
            }
        )
        run_map.append({**item, "run_id": run_id, "model_id": model_id, "selection_score": item_selection_score})

    if best_model_id is None:
        raise ValueError("Training completed but no best model was created.")

    if payload.auto_activate_best:
        model_repository.activate_model(best_model_id)
        from app.repositories import project_state_repository

        project_state_repository.update_state(payload.project_id, current_model_id=best_model_id)
    from app.repositories import dataset_repository

    if payload.dataset_id:
        dataset_repository.update_status(payload.dataset_id, "TRAINED")
    log_action(
        "ml.production_training.completed",
        "MLModel",
        best_model_id,
        payload.project_id,
        details={"trained": trained, "best": best, "failed": failed, "warnings": warning_messages},
    )
    production_model = model_repository.get_model(best_model_id)
    best_run = next(item for item in run_map if item["model_id"] == best_model_id)
    return {
        "production_model": production_model,
        "best_model_id": best_model_id,
        "best_model_type": best["model_type"],
        "best_model_key": best["model_type"],
        "best_model_name": best["model_name"],
        "selected_models": selected_models,
        "training_profile": payload.training_profile,
        "selection_strategy": payload.training_profile,
        "selection_metric": selection_metric,
        "selection_score": selection_score,
        "selection_reason": selection_reason,
        "reason_for_selection": best.get("reason_for_selection") or selection_reason,
        "threshold": best["threshold"],
        "selected_threshold": best["threshold"],
        "threshold_strategy": threshold_config.strategy,
        "threshold_config": threshold_config.__dict__,
        "threshold_metrics": best.get("threshold_metrics"),
        "threshold_candidates_top_5": best.get("threshold_candidates_top_5", []),
        "metrics": _metrics_subset(best),
        "model_comparison": run_map,
        "comparison": run_map,
        "failed_models": failed,
        "warnings": warning_messages,
        "feature_columns": SAFE_MODEL_FEATURE_COLUMNS,
        "excluded_leakage_columns": EXCLUDED_LEAKAGE_COLUMNS,
        "artifact_path": best_run["artifact_path"],
        "metadata_path": best_run["metadata_path"],
        "metadata": {**common_metadata, "metrics": _metrics_subset(best), "threshold": best["threshold"]},
        "auto_activated": bool(payload.auto_activate_best),
        "models": model_repository.list_models(),
        "training_runs": model_repository.list_training_runs(),
    }


def list_models():
    return model_repository.list_models()


def get_model(model_id: int):
    return model_repository.get_model(model_id)


def activate(model_id: int):
    model_repository.activate_model(model_id)
    from app.repositories import project_state_repository

    model = model_repository.get_model(model_id)
    project_state_repository.update_state(1, current_model_id=model_id)
    log_action("ml.model.activated", "MLModel", model_id)
    return model


def training_runs():
    return model_repository.list_training_runs()


def training_run(run_id: int):
    return model_repository.get_training_run(run_id)


def comparison(dataset_id: int | None = None):
    return model_repository.comparison(dataset_id)


def delete_model(model_id: int):
    affected = model_repository.soft_delete_model(model_id)
    log_action("ml.model.deleted", "MLModel", model_id, details={"soft_deleted": True})
    return {"deleted": affected > 0}


def delete_training_run(run_id: int):
    affected = model_repository.soft_delete_training_run(run_id)
    log_action("ml.training_run.deleted", "TrainingRun", run_id, details={"soft_deleted": True})
    return {"deleted": affected > 0}


def restore_training_run(run_id: int):
    affected = model_repository.restore_training_run(run_id)
    log_action("ml.training_run.restored", "TrainingRun", run_id, details={"restored": True})
    return {"restored": affected > 0}


def trainable_datasets(project_id: int):
    from app.services.dataset_service import trainable

    return trainable(project_id)


def training_guide():
    return {
        "title": "How to train DefectAI models",
        "profiles": profile_metadata(),
        "steps": [
            "Upload a dataset containing module_name, loc, complexity, coupling, code_churn, defect_label.",
            "defect_label must use 0 for No Defect and 1 for Defect.",
            "DefectAI excludes leakage-prone columns such as defect_count, defect_density, labels, and prediction outputs from model features.",
            "Choose Logistic Regression, Random Forest, Neural Network, or train all models.",
            "Select a training profile to tune threshold and best-model ranking for the product goal.",
            "Prediction uses the tuned artifact threshold, not a hardcoded 0.5 threshold.",
        ],
    }

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
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from app.ml.feature_engineering import P7_FEATURE_COLUMNS, build_p7_features
from app.repositories import metric_repository, model_repository
from app.schemas.model_schema import TrainingRequest
from app.services.audit_service import log_action

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
PRODUCTION_ARTIFACT = ARTIFACT_DIR / "defectai_p7_production.joblib"
PRODUCTION_METADATA = ARTIFACT_DIR / "defectai_p7_production_metadata.json"
PRODUCTION_THRESHOLD = 0.5
MIN_TRAINING_RECORDS = 4
SMALL_DATASET_WARNING_THRESHOLD = 20
MLP_EARLY_STOPPING_MIN_ROWS = 50
logger = logging.getLogger(__name__)

MODEL_NAMES = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "neural_network": "Neural Networks",
}


def _estimator(model_type: str, payload: TrainingRequest, training_rows: int | None = None):
    if model_type == "logistic_regression":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=max(payload.max_iter, 1000),
                        class_weight="balanced",
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
                        n_estimators=300,
                        max_depth=None,
                        class_weight="balanced_subsample",
                        random_state=payload.random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
    if model_type == "neural_network":
        hidden = int(payload.hidden_layer_size)
        early_stopping = training_rows is None or training_rows >= MLP_EARLY_STOPPING_MIN_ROWS
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    MLPClassifier(
                        hidden_layer_sizes=(hidden, max(8, hidden // 2)),
                        activation="relu",
                        max_iter=payload.max_iter,
                        early_stopping=early_stopping,
                        validation_fraction=0.15,
                        n_iter_no_change=20,
                        random_state=payload.random_state,
                    ),
                ),
            ]
        )
    raise ValueError(f"Unsupported model: {model_type}")


def _types(payload: TrainingRequest):
    if payload.model_types:
        return payload.model_types
    if payload.model_type and payload.model_type != "all":
        return [payload.model_type]
    return ["logistic_regression", "random_forest", "neural_network"]


def _safe_roc_auc(y_true, probabilities) -> float:
    return float(roc_auc_score(y_true, probabilities)) if pd.Series(y_true).nunique() == 2 else 0.0


def _classification_metrics(y_true, y_pred, probabilities) -> dict:
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": f1,
        "f1_score": f1,
        "roc_auc": _safe_roc_auc(y_true, probabilities),
    }


def _evaluate_estimator(estimator, X_test, y_test):
    y_pred = estimator.predict(X_test)
    probabilities = np.clip(estimator.predict_proba(X_test)[:, 1].astype(float), 0.0, 1.0)
    return y_pred, probabilities, _classification_metrics(y_test, y_pred, probabilities)


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
    }
    try:
        scores = cross_validate(estimator, X, y, scoring=scoring, cv=cv, n_jobs=None, error_score=np.nan)
    except Exception as exc:
        logger.exception("Cross-validation failed for %s", model_type)
        return {"enabled": False, "reason": str(exc)}
    result = {"enabled": True, "folds": n_splits}
    for metric_name in scoring:
        values = np.asarray(scores.get(f"test_{metric_name}", []), dtype=float)
        result[f"{metric_name}_mean"] = float(np.nanmean(values)) if values.size else 0.0
        result[f"{metric_name}_std"] = float(np.nanstd(values)) if values.size else 0.0
    return result


def _feature_importance(estimator, X_test: pd.DataFrame, y_test: pd.Series, payload: TrainingRequest) -> dict:
    model = estimator.named_steps.get("model") if hasattr(estimator, "named_steps") else estimator
    result: dict = {"feature_importance": [], "permutation_importance": []}
    if hasattr(model, "feature_importances_"):
        result["feature_importance"] = [
            {"feature": feature, "importance": float(importance)}
            for feature, importance in sorted(
                zip(P7_FEATURE_COLUMNS, model.feature_importances_),
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
                scoring="roc_auc",
            )
            result["permutation_importance"] = [
                {"feature": feature, "importance_mean": float(mean), "importance_std": float(std)}
                for feature, mean, std in sorted(
                    zip(P7_FEATURE_COLUMNS, perm.importances_mean, perm.importances_std),
                    key=lambda item: float(item[1]),
                    reverse=True,
                )
            ]
        except Exception as exc:
            logger.warning("Permutation importance skipped: %s", exc)
            result["permutation_importance_error"] = str(exc)
    return result


def _prepare_training_frame(payload: TrainingRequest):
    rows = metric_repository.training_records(payload.project_id, payload.dataset_id)

    if len(rows) < MIN_TRAINING_RECORDS:
        raise ValueError(
            f"Dataset has only {len(rows)} labeled records. "
            f"At least {MIN_TRAINING_RECORDS} labeled rows are required, with at least 2 rows in each label class."
        )

    df = build_p7_features(pd.DataFrame(rows), use_label_density=False)

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
        raise ValueError(
            "Training requires at least 2 records for each label class so stratified train/test split can run."
        )

    logger.info(
        "Training dataset prepared: rows=%s, no_defect=%s, defect=%s, features=%s",
        len(df),
        int(label_counts.get(0, 0)),
        int(label_counts.get(1, 0)),
        len(P7_FEATURE_COLUMNS),
    )

    X = df.reindex(columns=P7_FEATURE_COLUMNS).apply(pd.to_numeric, errors="coerce")
    y = df["defect_label"].astype(int)
    stratify = y if y.nunique() == 2 and y.value_counts().min() >= 2 else None
    warnings = list(df.attrs.get("warnings", []))
    if len(df) < SMALL_DATASET_WARNING_THRESHOLD:
        warnings.append(
            f"Small training dataset: {len(df)} labeled rows. Artifact is valid for testing, but collect more data before production use."
        )

    split_test_size = payload.test_size
    minimum_stratified_test_size = 2 / len(y)
    if stratify is not None and split_test_size < minimum_stratified_test_size:
        split_test_size = min(0.5, minimum_stratified_test_size)
        warnings.append(
            f"Adjusted test_size from {payload.test_size} to {round(split_test_size, 4)} so the stratified test split contains both classes."
        )

    split = train_test_split(
        X,
        y,
        test_size=split_test_size,
        random_state=payload.random_state,
        stratify=stratify,
    )
    dataset_profile = {
        "row_count": int(len(df)),
        "class_distribution": {str(k): int(v) for k, v in label_counts.to_dict().items()},
        "feature_warnings": warnings,
        "requested_test_size": payload.test_size,
        "effective_test_size": split_test_size,
    }
    return (*split, dataset_profile)


def train(payload: TrainingRequest):
    return train_production(payload, model_types=_types(payload))


def train_production(payload: TrainingRequest, model_types: list[str] | None = None):
    X_train, X_test, y_train, y_test, dataset_profile = _prepare_training_frame(payload)
    X_all = pd.concat([X_train, X_test], axis=0)
    y_all = pd.concat([y_train, y_test], axis=0)

    trained = []
    version = datetime.now().strftime("v%Y%m%d%H%M%S")
    created_at = datetime.now().isoformat()
    fitted_estimators = {}
    warning_messages = list(dataset_profile.get("feature_warnings", []))

    for model_type in (model_types or ["logistic_regression", "random_forest", "neural_network"]):
        estimator = _estimator(model_type, payload, training_rows=len(X_train))
        start = time.perf_counter()
        estimator.fit(X_train, y_train)
        training_seconds = time.perf_counter() - start

        train_pred, train_probabilities, train_metrics = _evaluate_estimator(estimator, X_train, y_train)
        pred_start = time.perf_counter()
        y_pred, probabilities, metrics = _evaluate_estimator(estimator, X_test, y_test)
        latency_ms = ((time.perf_counter() - pred_start) / max(len(X_test), 1)) * 1000
        cv_metrics = _cross_validation_metrics(model_type, X_all, y_all, payload)
        importance = _feature_importance(estimator, X_test, y_test, payload) if model_type == "random_forest" else {}
        overfit_gap = round(float(train_metrics["roc_auc"] - metrics["roc_auc"]), 4)
        if overfit_gap > 0.15:
            warning_messages.append(
                f"{MODEL_NAMES[model_type]} may be overfitting: train ROC-AUC exceeds test ROC-AUC by {overfit_gap}."
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
            "confusion_matrix": confusion_matrix(y_test, y_pred, labels=[0, 1]).astype(int).tolist(),
            **importance,
        }
        trained.append(
            {
                "model_type": model_type,
                "model_name": MODEL_NAMES[model_type],
                "latency_ms": round(latency_ms, 4),
                "training_time_seconds": round(training_seconds, 4),
                "confusion_matrix": fitted_estimators[model_type]["confusion_matrix"],
                "train_metrics": train_metrics,
                "cross_validation": cv_metrics,
                "overfit_gap": overfit_gap,
                **importance,
                **metrics,
            }
        )

    best = max(trained, key=lambda item: (item["roc_auc"], item["f1_score"], item["recall"]))
    best_fit = fitted_estimators[best["model_type"]]
    if any(round(float(item["accuracy"]), 6) >= 1.0 for item in trained):
        warning_messages.append("Perfect accuracy detected. Dataset may be too small, duplicated, or too easy. Validate with another dataset.")

    metadata = {
        "artifact_schema_version": 1,
        "name": model_repository.PRODUCTION_MODEL_NAME,
        "version": version,
        "model_type": best["model_type"],
        "best_model_type": best["model_type"],
        "model_name": MODEL_NAMES[best["model_type"]],
        "feature_columns": P7_FEATURE_COLUMNS,
        "metrics": {key: best[key] for key in ["accuracy", "precision", "recall", "f1", "f1_score", "roc_auc"]},
        "threshold": PRODUCTION_THRESHOLD,
        "selection_metric": "roc_auc_then_f1",
        "comparison": trained,
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
    artifact_payload = {
        "estimator": best_fit["estimator"],
        "feature_columns": P7_FEATURE_COLUMNS,
        "metadata": metadata,
    }
    joblib.dump(artifact_payload, PRODUCTION_ARTIFACT)
    PRODUCTION_METADATA.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    model_id = model_repository.upsert_production_model(
        {
            "name": model_repository.PRODUCTION_MODEL_NAME,
            "model_type": best["model_type"],
            "version": version,
            "artifact_path": str(PRODUCTION_ARTIFACT),
            "is_active": 1,
            "latency_ms": best["latency_ms"],
            "hyperparameters_json": json.dumps(
                {
                    **payload.model_dump(),
                    "production_metadata": str(PRODUCTION_METADATA),
                    "threshold": PRODUCTION_THRESHOLD,
                    "selection_metric": "roc_auc_then_f1",
                    "sklearn_version": sklearn.__version__,
                },
                ensure_ascii=False,
            ),
            "feature_list_json": json.dumps(P7_FEATURE_COLUMNS),
            **{key: best[key] for key in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]},
        }
    )

    run_map = []
    for item in trained:
        run_id = model_repository.create_training_run(
            {
                "model_id": model_id,
                "dataset_id": payload.dataset_id,
                "model_type": item["model_type"],
                "model_version": version,
                "train_size": len(X_train),
                "test_size": len(X_test),
                "confusion_matrix_json": json.dumps(item["confusion_matrix"]),
                "training_time_seconds": item["training_time_seconds"],
                "parameters_json": json.dumps(
                    {
                        "feature_columns": P7_FEATURE_COLUMNS,
                        **payload.model_dump(),
                        "warnings": warning_messages,
                        "threshold": PRODUCTION_THRESHOLD,
                        "cross_validation": item.get("cross_validation"),
                        "train_metrics": item.get("train_metrics"),
                        "overfit_gap": item.get("overfit_gap"),
                    },
                    ensure_ascii=False,
                ),
                "started_at": datetime.now(),
                "completed_at": datetime.now(),
                **{key: item[key] for key in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]},
            }
        )
        run_map.append({**item, "run_id": run_id, "model_id": model_id})

    if payload.auto_activate_best:
        model_repository.activate_model(model_id)
        from app.repositories import project_state_repository

        project_state_repository.update_state(payload.project_id, current_model_id=model_id)
    from app.repositories import dataset_repository

    if payload.dataset_id:
        dataset_repository.update_status(payload.dataset_id, "TRAINED")
    log_action("ml.production_training.completed", "MLModel", model_id, payload.project_id, details={"trained": trained, "best": best, "warnings": warning_messages})
    production_model = model_repository.get_model(model_id)
    return {
        "production_model": production_model,
        "best_model_id": model_id,
        "best_model_type": best["model_type"],
        "comparison": run_map,
        "warnings": warning_messages,
        "feature_columns": P7_FEATURE_COLUMNS,
        "artifact_path": str(PRODUCTION_ARTIFACT),
        "metadata_path": str(PRODUCTION_METADATA),
        "metadata": metadata,
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
    state_project_id = 1
    project_state_repository.update_state(state_project_id, current_model_id=model_id)
    log_action("ml.model.activated", "MLModel", model_id)
    return model


def training_runs():
    return model_repository.list_training_runs()


def training_run(run_id: int):
    return model_repository.get_training_run(run_id)


def comparison():
    return model_repository.comparison()


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
        "steps": [
            "Upload a dataset containing module_name, loc, complexity, coupling, code_churn, defect_label.",
            "defect_label must use 0 for No Defect and 1 for Defect.",
            "Choose a training dataset and train one model or all models.",
            "DefectAI compares Accuracy, Precision, Recall, F1-score, ROC-AUC and activates the best ROC-AUC then F1-score model.",
            "Return to Metrics Explorer and analyze a dataset with the active model.",
        ],
    }

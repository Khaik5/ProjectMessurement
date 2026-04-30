from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
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

MODEL_NAMES = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "neural_network": "Neural Networks",
}


def _estimator(model_type: str, payload: TrainingRequest):
    if model_type == "logistic_regression":
        return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    if model_type == "random_forest":
        return Pipeline([("imputer", SimpleImputer(strategy="median")), ("model", RandomForestClassifier(n_estimators=300, max_depth=None, class_weight="balanced", random_state=payload.random_state))])
    if model_type == "neural_network":
        return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu", max_iter=1000, random_state=payload.random_state))])
    raise ValueError(f"Unsupported model: {model_type}")


def _types(payload: TrainingRequest):
    if payload.model_types:
        return payload.model_types
    if payload.model_type and payload.model_type != "all":
        return [payload.model_type]
    return ["logistic_regression", "random_forest", "neural_network"]


def _evaluate_estimator(estimator, X_test, y_test):
    y_pred = estimator.predict(X_test)
    probabilities = estimator.predict_proba(X_test)[:, 1]
    return y_pred, probabilities, {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)) if y_test.nunique() == 2 else 0.0,
    }


def _prepare_training_frame(payload: TrainingRequest):
    rows = metric_repository.training_records(payload.project_id, payload.dataset_id)
    if len(rows) < 20:
        raise ValueError("Not enough labeled MetricRecords (minimum 20). Upload a dataset with defect_label (0/1).")

    df = build_p7_features(pd.DataFrame(rows), use_label_density=False)
    if "defect_label" not in df.columns:
        raise ValueError("Training requires defect_label column with values 0/1.")
    if df["defect_label"].nunique() < 2:
        raise ValueError("Training dataset must contain both defect_label 0 and 1.")
    X = df[P7_FEATURE_COLUMNS]
    y = df["defect_label"].astype(int)
    stratify = y if y.nunique() == 2 and y.value_counts().min() >= 2 else None
    return train_test_split(X, y, test_size=payload.test_size, random_state=payload.random_state, stratify=stratify)


def train(payload: TrainingRequest):
    return train_production(payload, model_types=_types(payload))


def train_production(payload: TrainingRequest, model_types: list[str] | None = None):
    X_train, X_test, y_train, y_test = _prepare_training_frame(payload)

    trained = []
    version = datetime.now().strftime("v%Y%m%d%H%M%S")
    fitted_estimators = {}
    for model_type in (model_types or ["logistic_regression", "random_forest", "neural_network"]):
        estimator = _estimator(model_type, payload)
        start = time.perf_counter()
        estimator.fit(X_train, y_train)
        training_seconds = time.perf_counter() - start
        pred_start = time.perf_counter()
        y_pred, probabilities, metrics = _evaluate_estimator(estimator, X_test, y_test)
        latency_ms = ((time.perf_counter() - pred_start) / max(len(X_test), 1)) * 1000
        fitted_estimators[model_type] = {
            "estimator": estimator,
            "latency_ms": round(latency_ms, 4),
            "training_time_seconds": round(training_seconds, 4),
            "y_pred": y_pred,
            "metrics": metrics,
            "confusion_matrix": confusion_matrix(y_test, y_pred, labels=[0, 1]).astype(int).tolist(),
        }
        trained.append(
            {
                "model_type": model_type,
                "model_name": MODEL_NAMES[model_type],
                "latency_ms": round(latency_ms, 4),
                "training_time_seconds": round(training_seconds, 4),
                "confusion_matrix": fitted_estimators[model_type]["confusion_matrix"],
                **metrics,
            }
        )

    best = max(trained, key=lambda item: (item["f1_score"], item["roc_auc"], item["precision"]))
    best_fit = fitted_estimators[best["model_type"]]
    warning_messages = []
    if any(round(float(item["accuracy"]), 6) >= 1.0 for item in trained):
        warning_messages.append("Perfect score detected. Dataset may be too small, duplicated, or too easy. Please validate with another dataset.")

    artifact_payload = {
        "estimator": best_fit["estimator"],
        "feature_columns": P7_FEATURE_COLUMNS,
        "model_type": best["model_type"],
        "version": version,
    }
    joblib.dump(artifact_payload, PRODUCTION_ARTIFACT)
    metadata = {
        "name": model_repository.PRODUCTION_MODEL_NAME,
        "version": version,
        "feature_columns": P7_FEATURE_COLUMNS,
        "best_model_type": best["model_type"],
        "comparison": trained,
        "warnings": warning_messages,
        "dataset_id": payload.dataset_id,
        "test_size": payload.test_size,
        "random_state": payload.random_state,
        "created_at": datetime.now().isoformat(),
    }
    PRODUCTION_METADATA.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    model_id = model_repository.upsert_production_model(
        {
            "name": model_repository.PRODUCTION_MODEL_NAME,
            "model_type": best["model_type"],
            "version": version,
            "artifact_path": str(PRODUCTION_ARTIFACT),
            "is_active": 1,
            "latency_ms": best["latency_ms"],
            "hyperparameters_json": json.dumps({**payload.model_dump(), "production_metadata": str(PRODUCTION_METADATA)}, ensure_ascii=False),
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
                "parameters_json": json.dumps({"feature_columns": P7_FEATURE_COLUMNS, **payload.model_dump(), "warnings": warning_messages}, ensure_ascii=False),
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
            "DefectAI compares Accuracy, Precision, Recall, F1-score, ROC-AUC and activates the best F1-score model.",
            "Return to Metrics Explorer and analyze a dataset with the active model.",
        ],
    }

from __future__ import annotations

import os
import logging

import joblib
import numpy as np
import pandas as pd

from app.ml.feature_contract import EXCLUDED_LEAKAGE_COLUMNS, SAFE_MODEL_FEATURE_COLUMNS, assert_safe_model_features
from app.ml.feature_engineering import build_p7_features
from app.repositories import dataset_repository, metric_repository, model_repository, prediction_repository, project_state_repository
from app.schemas.prediction_schema import PredictionRunRequest, PredictionSingleRequest
from app.services.audit_service import log_action
from app.utils.measurement_utils import measurement_fallback_message
from app.utils.risk_utils import classify_risk, prediction_label

logger = logging.getLogger(__name__)

MODEL_SOURCE_AI = "AI production model"
MODEL_SOURCE_FALLBACK = "Measurement fallback"
DEFAULT_THRESHOLD = 0.5


def _active_estimator(model_id: int | None = None):
    model = model_repository.get_model(model_id) if model_id else model_repository.get_active_production_model()
    if not model:
        return None, None, "fallback_no_active_model"
    artifact = model.get("artifact_path")
    if not artifact or not os.path.exists(artifact):
        return model, None, "fallback_missing_artifact"
    try:
        artifact_payload = joblib.load(artifact)
    except Exception as exc:
        logger.exception("Failed to load ML artifact at %s", artifact)
        return model, None, f"fallback_artifact_unavailable: {exc}"
    if isinstance(artifact_payload, dict) and "estimator" in artifact_payload:
        return model, artifact_payload, MODEL_SOURCE_AI
    return model, {"estimator": artifact_payload, "feature_columns": SAFE_MODEL_FEATURE_COLUMNS}, MODEL_SOURCE_AI


def _predict_probabilities(estimator_payload, features: pd.DataFrame):
    if not estimator_payload:
        return None, [], SAFE_MODEL_FEATURE_COLUMNS
    estimator = estimator_payload["estimator"]
    if not hasattr(estimator, "predict_proba"):
        raise ValueError("Active estimator does not support predict_proba")
    metadata = estimator_payload.get("metadata") or {}
    feature_columns = estimator_payload.get("feature_columns") or metadata.get("feature_columns") or SAFE_MODEL_FEATURE_COLUMNS
    warnings = []
    if feature_columns != SAFE_MODEL_FEATURE_COLUMNS:
        message = (
            "Artifact feature_columns differ from current SAFE_MODEL_FEATURE_COLUMNS. "
            "Using artifact order for backward-compatible prediction."
        )
        logger.warning(message)
        warnings.append(message)
        unsafe = [column for column in feature_columns if column in EXCLUDED_LEAKAGE_COLUMNS]
        if unsafe:
            message = f"Legacy artifact contains leakage-prone columns: {', '.join(unsafe)}. Retrain production model."
            logger.warning(message)
            warnings.append(message)
    else:
        assert_safe_model_features(feature_columns)
    missing = [column for column in feature_columns if column not in features.columns]
    if missing:
        message = f"Prediction features missing columns filled with 0: {', '.join(missing)}"
        logger.warning(message)
        warnings.append(message)
    X = features.reindex(columns=feature_columns)
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    probabilities = estimator.predict_proba(X)[:, 1]
    return np.clip(probabilities.astype(float), 0.0, 1.0), warnings, feature_columns


def _threshold(estimator_payload) -> float:
    metadata = estimator_payload.get("metadata") if isinstance(estimator_payload, dict) else None
    value = (metadata or {}).get("threshold", DEFAULT_THRESHOLD)
    try:
        value = float(value)
    except (TypeError, ValueError):
        logger.warning("Artifact threshold missing or invalid; using default %.2f", DEFAULT_THRESHOLD)
        return DEFAULT_THRESHOLD
    if 0.0 < value < 1.0:
        return value
    logger.warning("Artifact threshold %.4f out of range; using default %.2f", value, DEFAULT_THRESHOLD)
    return DEFAULT_THRESHOLD


def _prediction_value(probability: float, threshold: float) -> int:
    return int(float(probability) >= threshold)


def _heatmap_payload(results: list[dict], model_source: str) -> dict:
    heatmap = [
        {
            "x": row.get("module_name"),
            "y": "defect_probability",
            "value": float(row.get("defect_probability") or 0.0),
            "risk_level": row.get("risk_level"),
        }
        for row in results
    ]
    probabilities = [float(row.get("defect_probability") or 0.0) for row in results]
    high_risk_count = sum(1 for row in results if row.get("risk_level") in {"HIGH", "CRITICAL"})
    return {
        "heatmap": heatmap,
        "summary": {
            "total_modules": len(results),
            "high_risk_count": high_risk_count,
            "average_defect_probability": round(float(np.mean(probabilities)), 4) if probabilities else 0.0,
            "model_source": model_source,
        },
    }


def _risk_id(level: str) -> int:
    risk_id = prediction_repository.get_risk_level_id(level)
    if not risk_id:
        raise ValueError(f"Risk level not found in SQL Server: {level}")
    return risk_id


def predict_single(payload: PredictionSingleRequest):
    model, estimator, source = _active_estimator(payload.model_id)
    features = build_p7_features([payload.model_dump()], use_label_density=False)
    measurement_risk = float(features.iloc[0]["risk_score"])
    ml_probs = None
    prediction_warnings = list(features.attrs.get("warnings", []))
    try:
        ml_probs, model_warnings, feature_columns = _predict_probabilities(estimator, features)
        prediction_warnings.extend(model_warnings)
    except Exception as exc:
        logger.exception("Prediction failed with active model; falling back to measurement risk")
        source = f"fallback_model_error: {exc}"
        feature_columns = SAFE_MODEL_FEATURE_COLUMNS
    used_active = ml_probs is not None
    threshold = _threshold(estimator) if used_active else DEFAULT_THRESHOLD
    prob = round(float(ml_probs[0]) if used_active else measurement_risk, 4)
    prob = max(0.0, min(1.0, prob))
    risk = classify_risk(prob)
    row = features.iloc[0].to_dict()
    predicted = _prediction_value(prob, threshold)
    prediction_id = prediction_repository.insert_prediction(
        {
            "project_id": payload.project_id,
            "dataset_id": None,
            "model_id": model["id"] if model and used_active else None,
            "module_name": payload.module_name,
            "loc": payload.loc,
            "complexity": payload.complexity,
            "coupling": payload.coupling,
            "code_churn": payload.code_churn,
            "defect_probability": prob,
            "prediction": predicted,
            "prediction_label": prediction_label(prob),
            "risk_score": measurement_risk,
            "defect_density": row.get("defect_density"),
            "size_score": row.get("size_score"),
            "complexity_score": row.get("complexity_score"),
            "coupling_score": row.get("coupling_score"),
            "churn_score": row.get("churn_score"),
            "risk_level_id": _risk_id(risk["name"]),
            "suggested_action": risk["suggested_action"],
        }
    )
    log_action("prediction.single", "Prediction", prediction_id, payload.project_id, details={"model_source": source})
    model_source = MODEL_SOURCE_AI if used_active else MODEL_SOURCE_FALLBACK
    return {
        **row,
        "id": prediction_id,
        "defect_probability": prob,
        "prediction": predicted,
        "prediction_label_numeric": predicted,
        "prediction_label": prediction_label(prob),
        "risk_score": measurement_risk,
        "risk_level": risk["name"],
        "suggested_action": risk["suggested_action"],
        "model_source": model_source,
        "model_used": model.get("name") if model and used_active else "Measurement-based fallback",
        "used_fallback": not used_active,
        "fallback_reason": None if used_active else source,
        "threshold": threshold,
        "feature_columns": feature_columns,
        "warnings": prediction_warnings,
        "message": measurement_fallback_message(used_active, source),
    }


def predict_batch(payload: PredictionRunRequest):
    model, estimator, source = _active_estimator(payload.model_id)
    metrics = metric_repository.list_by_dataset(payload.dataset_id)
    if not metrics:
        raise ValueError("Dataset has no MetricRecords to analyze.")
    features = build_p7_features(pd.DataFrame(metrics), use_label_density=False)
    prediction_warnings = list(features.attrs.get("warnings", []))
    try:
        ml_probs, model_warnings, feature_columns = _predict_probabilities(estimator, features)
        prediction_warnings.extend(model_warnings)
    except Exception as exc:
        logger.exception("Batch prediction failed with active model; falling back to measurement risk")
        estimator = None
        ml_probs = None
        source = f"fallback_model_error: {exc}"
        feature_columns = SAFE_MODEL_FEATURE_COLUMNS
    prediction_repository.delete_by_dataset(payload.dataset_id)
    rows = []
    results = []
    used_active = ml_probs is not None
    threshold = _threshold(estimator) if used_active else DEFAULT_THRESHOLD
    model_source = MODEL_SOURCE_AI if used_active else MODEL_SOURCE_FALLBACK
    for idx, feature in features.reset_index(drop=True).iterrows():
        measurement_risk = round(float(feature.get("risk_score") or 0.0), 4)
        ml_prob = float(ml_probs[idx]) if used_active else None
        prob = round(ml_prob if used_active else measurement_risk, 4)
        prob = max(0.0, min(1.0, prob))
        risk = classify_risk(prob)
        risk_id = _risk_id(risk["name"])
        label = prediction_label(prob)
        predicted = _prediction_value(prob, threshold)
        rows.append(
            (
                payload.project_id,
                payload.dataset_id,
                model["id"] if model and used_active else None,
                feature["module_name"],
                int(feature["loc"]),
                float(feature["complexity"]),
                float(feature["coupling"]),
                float(feature["code_churn"]),
                prob,
                predicted,
                label,
                float(measurement_risk),
                None if pd.isna(feature.get("defect_density")) else float(feature.get("defect_density")),
                float(feature.get("size_score") or 0),
                float(feature.get("complexity_score") or 0),
                float(feature.get("coupling_score") or 0),
                float(feature.get("churn_score") or 0),
                risk_id,
                risk["suggested_action"],
            )
        )
        results.append(
            {
                **feature.to_dict(),
                "defect_probability": prob,
                "prediction": predicted,
                "prediction_label_numeric": predicted,
                "prediction_label": label,
                "risk_score": float(measurement_risk),
                "risk_level": risk["name"],
                "suggested_action": risk["suggested_action"],
                "model_source": model_source,
                "model_used": model.get("name") if model and used_active else "Measurement-based fallback",
                "used_fallback": not used_active,
                "threshold": threshold,
            }
        )
    prediction_repository.insert_predictions(rows)
    dataset_repository.update_status(payload.dataset_id, "ANALYZED")
    project_state_repository.update_state(
        payload.project_id,
        current_dataset_id=payload.dataset_id,
        current_analysis_dataset_id=payload.dataset_id,
        current_model_id=model["id"] if model and used_active else None,
    )
    log_action("prediction.batch", "Prediction", None, payload.project_id, details={"dataset_id": payload.dataset_id, "rows": len(rows), "model_source": source})
    heatmap_data = _heatmap_payload(results, model_source)
    return {
        "dataset_id": payload.dataset_id,
        "total_modules": len(results),
        "predictions_created": len(rows),
        "used_model": model.get("name") if model and used_active else "Measurement-based fallback",
        "model_source": model_source,
        "fallback_reason": None if used_active else source,
        "used_fallback": not used_active,
        "threshold": threshold,
        "feature_columns": feature_columns,
        "warnings": prediction_warnings,
        "message": "Dataset analyzed successfully" if used_active else measurement_fallback_message(False, source),
        "results": results,
        **heatmap_data,
    }


def list_predictions(limit: int = 500):
    return prediction_repository.list_predictions(limit)


def project_predictions(project_id: int):
    return prediction_repository.by_project(project_id)


def dataset_predictions(dataset_id: int):
    dataset = dataset_repository.get_dataset(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset #{dataset_id} not found")
    rows = prediction_repository.by_dataset(dataset_id)
    heatmap_data = _heatmap_payload(
        rows,
        MODEL_SOURCE_FALLBACK if rows and all(row.get("model_id") is None for row in rows) else MODEL_SOURCE_AI,
    )
    return {
        "dataset_id": dataset_id,
        "rows": rows,
        "total": len(rows),
        "analyzed": bool(rows),
        **heatmap_data,
        "message": "OK" if rows else "Dataset has not been analyzed yet",
    }


def top_risk(project_id: int = 1, limit: int = 10):
    return prediction_repository.top_risk(project_id, limit)


def recent(limit: int = 20):
    return prediction_repository.recent(limit)

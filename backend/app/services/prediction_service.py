from __future__ import annotations

import os

import joblib
import pandas as pd

from app.ml.feature_engineering import P7_FEATURE_COLUMNS, build_p7_features
from app.repositories import dataset_repository, metric_repository, model_repository, prediction_repository, project_state_repository
from app.schemas.prediction_schema import PredictionRunRequest, PredictionSingleRequest
from app.services.audit_service import log_action
from app.utils.measurement_utils import measurement_fallback_message
from app.utils.risk_utils import classify_risk, prediction_label


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
        return model, None, f"fallback_artifact_unavailable: {exc}"
    if isinstance(artifact_payload, dict) and "estimator" in artifact_payload:
        return model, artifact_payload, "ai_production_model"
    return model, {"estimator": artifact_payload, "feature_columns": P7_FEATURE_COLUMNS}, "ai_production_model"


def _predict_probabilities(estimator_payload, features: pd.DataFrame):
    if not estimator_payload:
        return None
    estimator = estimator_payload["estimator"]
    feature_columns = estimator_payload.get("feature_columns") or P7_FEATURE_COLUMNS
    X = features.reindex(columns=feature_columns).fillna(0.0)
    return estimator.predict_proba(X)[:, 1]


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
    try:
        ml_probs = _predict_probabilities(estimator, features)
    except Exception:
        source = "fallback_model_error"
    used_active = ml_probs is not None
    prob = round((0.75 * float(ml_probs[0]) + 0.25 * measurement_risk), 4) if used_active else round(measurement_risk, 4)
    risk = classify_risk(prob)
    row = features.iloc[0].to_dict()
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
            "prediction": int(prob >= 0.5),
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
    return {
        **row,
        "id": prediction_id,
        "defect_probability": prob,
        "prediction": int(prob >= 0.5),
        "prediction_label": prediction_label(prob),
        "risk_score": measurement_risk,
        "risk_level": risk["name"],
        "suggested_action": risk["suggested_action"],
        "model_source": source,
        "message": measurement_fallback_message(used_active),
    }


def predict_batch(payload: PredictionRunRequest):
    model, estimator, source = _active_estimator(payload.model_id)
    metrics = metric_repository.list_by_dataset(payload.dataset_id)
    if not metrics:
        raise ValueError("Dataset has no MetricRecords to analyze.")
    features = build_p7_features(pd.DataFrame(metrics), use_label_density=False)
    try:
        ml_probs = _predict_probabilities(estimator, features)
    except Exception as exc:
        estimator = None
        ml_probs = None
        source = f"fallback_model_error: {exc}"
    prediction_repository.delete_by_dataset(payload.dataset_id)
    rows = []
    results = []
    used_active = ml_probs is not None
    for idx, feature in features.reset_index(drop=True).iterrows():
        measurement_risk = round(float(feature.get("risk_score") or 0.0), 4)
        ml_prob = float(ml_probs[idx]) if used_active else None
        prob = round((0.75 * ml_prob + 0.25 * measurement_risk), 4) if used_active else measurement_risk
        risk = classify_risk(prob)
        risk_id = _risk_id(risk["name"])
        label = prediction_label(prob)
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
                int(prob >= 0.5),
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
                "prediction": int(prob >= 0.5),
                "prediction_label": label,
                "risk_score": float(measurement_risk),
                "risk_level": risk["name"],
                "suggested_action": risk["suggested_action"],
                "model_source": "AI production model" if used_active else "Measurement fallback",
                "model_used": model.get("name") if model and used_active else "Measurement-based fallback",
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
    return {
        "dataset_id": payload.dataset_id,
        "total_modules": len(results),
        "predictions_created": len(rows),
        "used_model": model.get("name") if model and used_active else "Measurement-based fallback",
        "model_source": "AI production model" if used_active else source,
        "used_fallback": not used_active,
        "message": "Dataset analyzed successfully" if used_active else measurement_fallback_message(False),
        "results": results,
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
    return {
        "dataset_id": dataset_id,
        "rows": rows,
        "total": len(rows),
        "analyzed": bool(rows),
        "message": "OK" if rows else "Dataset has not been analyzed yet",
    }


def top_risk(project_id: int = 1, limit: int = 10):
    return prediction_repository.top_risk(project_id, limit)


def recent(limit: int = 20):
    return prediction_repository.recent(limit)

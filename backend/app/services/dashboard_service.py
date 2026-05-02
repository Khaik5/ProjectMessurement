from app.database import test_connection
from app.repositories import dashboard_repository, model_repository, prediction_repository
from app.repositories import project_state_repository
from app.services.metric_service import statistics


def resolve_dataset_id(project_id: int, dataset_id: int | None = None):
    if dataset_id:
        return dataset_id
    state = project_state_repository.get_state(project_id)
    return state.get("current_analysis_dataset_id") if state else None


def _empty(project_id: int):
    return {
        "dataset_name": None,
        "total_modules": 0,
        "predicted_defects": 0,
        "possible_defects": 0,
        "high_risk_count": 0,
        "critical_count": 0,
        "avg_defect_probability": 0.0,
        "avg_risk_score": 0.0,
        "active_model_name": None,
        "active_model_accuracy": 0.0,
        "used_fallback": False,
        "dataset": None,
        "database_status": test_connection(),
    }


def summary(project_id: int = 1, dataset_id: int | None = None):
    dataset_id = resolve_dataset_id(project_id, dataset_id)
    if not dataset_id:
        return _empty(project_id)
    raw = dashboard_repository.summary(project_id, dataset_id) or {}
    active = dashboard_repository.active_model()
    dataset = dashboard_repository.dataset_info(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset #{dataset_id} not found")
    has_predictions = int(raw.get("prediction_count") or 0) > 0
    metric_records_count = int(raw.get("total_modules") or 0)
    total_modules = metric_records_count if metric_records_count > 0 else int(dataset.get("row_count") or 0)
    used_fallback = bool(int(raw.get("used_fallback") or 0) == 1)
    message = "OK"
    if not has_predictions and metric_records_count > 0:
        message = "Dataset uploaded but not analyzed"
    elif not has_predictions and metric_records_count == 0:
        message = "Dataset metadata exists but has no MetricRecords. Re-upload the dataset to rebuild preview/analyze data."
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset.get("file_name") if dataset else None,
        "analyzed": has_predictions,
        "message": message,
        "total_modules": total_modules,
        "metric_records_count": metric_records_count,
        "predicted_defects": int(raw.get("defects_detected") or 0),
        "defect_count": int(raw.get("defects_detected") or 0),
        "no_defect_count": int(raw.get("no_defect_count") or 0),
        "possible_defects": int(raw.get("possible_defects") or 0),
        "possible_defect_count": int(raw.get("possible_defect_label_count") or 0),
        "possible_defect_label_count": int(raw.get("possible_defect_label_count") or 0),
        "high_risk_count": int(raw.get("high_risk") or 0),
        "critical_count": int(raw.get("critical_count") or 0),
        "avg_defect_probability": round(float(raw.get("avg_probability") or 0), 4),
        "avg_risk_score": round(float(raw.get("avg_risk_score") or 0), 4),
        "active_model_id": active.get("id") if active else None,
        "active_model_name": active.get("name") if active else None,
        "active_model_type": active.get("model_type") if active else None,
        "active_model_training_dataset_id": active.get("dataset_id") if active else None,
        "active_model_threshold": round(float(active.get("threshold") or 0), 4) if active else None,
        "active_model_accuracy": round(float(active.get("accuracy") or 0), 4) if active else round(float(raw.get("active_accuracy") or 0), 4),
        "active_model_precision": round(float(active.get("precision") or 0), 4) if active else 0.0,
        "active_model_recall": round(float(active.get("recall") or 0), 4) if active else 0.0,
        "active_model_f1_score": round(float(active.get("f1_score") or 0), 4) if active else 0.0,
        "active_model_roc_auc": round(float(active.get("roc_auc") or 0), 4) if active else 0.0,
        "active_model_pr_auc": round(float(active.get("pr_auc") or 0), 4) if active else 0.0,
        "prediction_model_id": raw.get("prediction_model_id"),
        "prediction_model_name": raw.get("prediction_model_name"),
        "stale_model_predictions": bool(raw.get("prediction_model_id") and active and int(raw.get("prediction_model_id")) != int(active.get("id"))),
        "used_fallback": bool(used_fallback),
        "prediction_count": int(raw.get("prediction_count") or 0),
        "dataset": dataset,
        "analysis_status": "ANALYZED" if has_predictions else "UPLOADED_NOT_ANALYZED",
        "metric_statistics": statistics(project_id, dataset_id),
        "database_status": test_connection(),
    }


def charts(project_id: int = 1, dataset_id: int | None = None):
    dataset_id = resolve_dataset_id(project_id, dataset_id)
    if not dataset_id:
        return {
            "risk_distribution": [],
            "top_risky_modules": [],
            "probability_trend": [],
            "risk_heatmap": [],
            "loc_complexity_scatter": [],
            "churn_probability": [],
            "coupling_distribution": [],
            "model_performance": [],
            "confusion_matrix": None,
            "critical_alerts": [],
        }
    summary_data = summary(project_id, dataset_id)
    if not summary_data.get("analyzed"):
        return {
            "risk_distribution": [],
            "top_risky_modules": [],
            "probability_trend": [],
            "risk_heatmap": [],
            "loc_complexity_scatter": [],
            "churn_probability": [],
            "coupling_distribution": [],
            "model_performance": model_performance(project_id),
            "confusion_matrix": None,
            "critical_alerts": [],
            "message": summary_data.get("message", "Dataset uploaded but not analyzed"),
            "analyzed": False,
        }
    confusion = dashboard_repository.latest_confusion_matrix_for_active_model()
    return {
        "risk_distribution": risk_distribution(project_id, dataset_id),
        "top_risky_modules": dashboard_repository.top_risky_modules(project_id, dataset_id, 10),
        "probability_trend": probability_trend(project_id, dataset_id),
        "risk_heatmap": dashboard_repository.risk_heatmap_v2(project_id, dataset_id, 80),
        "loc_complexity_scatter": dashboard_repository.loc_complexity_scatter(project_id, dataset_id, 200),
        "churn_probability": dashboard_repository.churn_probability(project_id, dataset_id),
        "coupling_distribution": dashboard_repository.coupling_distribution(project_id, dataset_id),
        "model_performance": model_performance(project_id),
        "confusion_matrix": confusion.get("confusion_matrix_json") if confusion else None,
        "critical_alerts": dashboard_repository.critical_alerts(project_id, dataset_id, 10),
        "message": "OK",
        "analyzed": True,
    }


def risk_distribution(project_id: int = 1, dataset_id: int | None = None):
    dataset_id = resolve_dataset_id(project_id, dataset_id)
    return dashboard_repository.risk_distribution(project_id, dataset_id) if dataset_id else []


def top_risk_modules(project_id: int = 1, dataset_id: int | None = None):
    dataset_id = resolve_dataset_id(project_id, dataset_id)
    return prediction_repository.top_risk(project_id, 10, dataset_id) if dataset_id else []


def probability_trend(project_id: int = 1, dataset_id: int | None = None):
    dataset_id = resolve_dataset_id(project_id, dataset_id)
    return dashboard_repository.probability_trend(project_id, dataset_id) if dataset_id else []


def risk_heatmap(project_id: int = 1, dataset_id: int | None = None):
    dataset_id = resolve_dataset_id(project_id, dataset_id)
    return dashboard_repository.risk_heatmap(project_id, dataset_id) if dataset_id else []


def model_performance(project_id: int = 1):
    return model_repository.comparison()

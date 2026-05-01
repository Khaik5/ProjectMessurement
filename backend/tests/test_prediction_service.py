import numpy as np

from app.ml.feature_engineering import P7_FEATURE_COLUMNS
from app.schemas.prediction_schema import PredictionRunRequest, PredictionSingleRequest
from app.services import prediction_service


class DummyEstimator:
    def __init__(self, probabilities):
        self.probabilities = probabilities

    def predict_proba(self, X):
        probs = np.asarray(self.probabilities[: len(X)], dtype=float)
        return np.column_stack([1.0 - probs, probs])


def _patch_prediction_repositories(monkeypatch, inserted_rows=None):
    monkeypatch.setattr(prediction_service.prediction_repository, "get_risk_level_id", lambda level: 1)
    monkeypatch.setattr(prediction_service.prediction_repository, "insert_prediction", lambda values: 123)
    monkeypatch.setattr(
        prediction_service.prediction_repository,
        "insert_predictions",
        lambda rows: inserted_rows.extend(rows) if inserted_rows is not None else len(rows),
    )
    monkeypatch.setattr(prediction_service.prediction_repository, "delete_by_dataset", lambda dataset_id: 1)
    monkeypatch.setattr(prediction_service.dataset_repository, "update_status", lambda dataset_id, status: 1)
    monkeypatch.setattr(prediction_service.project_state_repository, "update_state", lambda *args, **kwargs: 1)
    monkeypatch.setattr(prediction_service, "log_action", lambda *args, **kwargs: None)


def test_predict_single_missing_artifact_uses_measurement_fallback(monkeypatch):
    monkeypatch.setattr(prediction_service.model_repository, "get_active_production_model", lambda: None)
    _patch_prediction_repositories(monkeypatch)

    result = prediction_service.predict_single(
        PredictionSingleRequest(
            module_name="fallback_module",
            loc=100,
            complexity=20,
            coupling=5,
            code_churn=30,
        )
    )

    assert result["used_fallback"] is True
    assert result["model_source"] == "Measurement fallback"
    assert 0 <= result["defect_probability"] <= 1
    assert result["defect_probability"] == round(result["risk_score"], 4)
    assert "defect_probability" in result


def test_predict_single_uses_pure_predict_proba_probability(monkeypatch):
    estimator_payload = {
        "estimator": DummyEstimator([0.83]),
        "feature_columns": P7_FEATURE_COLUMNS,
        "metadata": {"threshold": 0.5},
    }
    monkeypatch.setattr(
        prediction_service,
        "_active_estimator",
        lambda model_id=None: ({"id": 7, "name": "DefectAI P7 Production Model"}, estimator_payload, "AI production model"),
    )
    _patch_prediction_repositories(monkeypatch)

    result = prediction_service.predict_single(
        PredictionSingleRequest(
            module_name="ml_module",
            loc=100,
            complexity=20,
            coupling=5,
            code_churn=30,
        )
    )

    assert result["used_fallback"] is False
    assert result["model_source"] == "AI production model"
    assert result["defect_probability"] == 0.83
    assert result["prediction"] == 1
    assert result["prediction_label"] == "Defect"


def test_predict_batch_returns_heatmap_ready_contract(monkeypatch):
    inserted_rows = []
    estimator_payload = {
        "estimator": DummyEstimator([0.2, 0.91]),
        "feature_columns": P7_FEATURE_COLUMNS,
        "metadata": {"threshold": 0.5},
    }
    metrics = [
        {"module_name": "module_a", "loc": 100, "complexity": 5, "coupling": 2, "code_churn": 10},
        {"module_name": "module_b", "loc": 900, "complexity": 55, "coupling": 20, "code_churn": 300},
    ]

    monkeypatch.setattr(
        prediction_service,
        "_active_estimator",
        lambda model_id=None: ({"id": 7, "name": "DefectAI P7 Production Model"}, estimator_payload, "AI production model"),
    )
    monkeypatch.setattr(prediction_service.metric_repository, "list_by_dataset", lambda dataset_id: metrics)
    _patch_prediction_repositories(monkeypatch, inserted_rows)

    result = prediction_service.predict_batch(PredictionRunRequest(project_id=1, dataset_id=99))

    assert result["used_fallback"] is False
    assert result["model_source"] == "AI production model"
    assert result["results"][0]["defect_probability"] == 0.2
    assert result["results"][1]["defect_probability"] == 0.91
    assert result["heatmap"][1] == {
        "x": "module_b",
        "y": "defect_probability",
        "value": 0.91,
        "risk_level": "CRITICAL",
    }
    assert result["summary"]["total_modules"] == 2
    assert result["summary"]["high_risk_count"] == 1
    assert len(inserted_rows) == 2

from app.ml.feature_contract import SAFE_MODEL_FEATURE_COLUMNS
from app.repositories import dataset_repository, project_state_repository
from app.schemas.model_schema import TrainingRequest
from app.services import ml_training_service


class FakePath:
    def __init__(self, name):
        self.name = name

    def write_text(self, text, encoding=None):
        self.text = text

    def __str__(self):
        return self.name


def _training_rows(count=40):
    rows = []
    for index in range(count):
        label = int(index % 2 == 1)
        rows.append(
            {
                "module_name": f"module_{index}",
                "loc": 120 + index * 8 + label * 250,
                "ncloc": 100 + index * 7 + label * 220,
                "cloc": 20,
                "complexity": 8 + label * 35 + index * 0.2,
                "cyclomatic_complexity": 8 + label * 35 + index * 0.2,
                "depth_of_nesting": 2 + label * 4,
                "coupling": 3 + label * 12,
                "cohesion": 0.8 - label * 0.4,
                "information_flow_complexity": 5 + label * 20,
                "code_churn": 20 + label * 220 + index,
                "change_request_backlog": label * 10,
                "pending_effort_hours": label * 12,
                "percent_reused": 0.6 - label * 0.3,
                "defect_count": label,
                "defect_label": label,
            }
        )
    return rows


def test_train_production_writes_contract_artifact_metadata(monkeypatch):
    artifact_path = FakePath("memory_production.joblib")
    metadata_path = FakePath("memory_production_metadata.json")
    captured = {}
    runs = []

    monkeypatch.setattr(ml_training_service, "PRODUCTION_ARTIFACT", artifact_path)
    monkeypatch.setattr(ml_training_service, "PRODUCTION_METADATA", metadata_path)
    monkeypatch.setattr(ml_training_service.joblib, "dump", lambda payload, path: captured.setdefault("artifact", payload))
    monkeypatch.setattr(ml_training_service.metric_repository, "training_records", lambda project_id, dataset_id: _training_rows())
    monkeypatch.setattr(ml_training_service.model_repository, "upsert_production_model", lambda values: 42)
    monkeypatch.setattr(
        ml_training_service.model_repository,
        "create_training_run",
        lambda values: runs.append(values) or len(runs),
    )
    monkeypatch.setattr(ml_training_service.model_repository, "activate_model", lambda model_id: 1)
    monkeypatch.setattr(
        ml_training_service.model_repository,
        "get_model",
        lambda model_id: {"id": model_id, "name": "DefectAI P7 Production Model", "is_active": True},
    )
    monkeypatch.setattr(ml_training_service.model_repository, "list_models", lambda: [])
    monkeypatch.setattr(ml_training_service.model_repository, "list_training_runs", lambda: [])
    monkeypatch.setattr(dataset_repository, "update_status", lambda dataset_id, status: 1)
    monkeypatch.setattr(project_state_repository, "update_state", lambda *args, **kwargs: 1)
    monkeypatch.setattr(ml_training_service, "log_action", lambda *args, **kwargs: None)

    result = ml_training_service.train_production(
        TrainingRequest(dataset_id=123, model_types=["logistic_regression"], max_iter=100),
        model_types=["logistic_regression"],
    )
    artifact = captured["artifact"]

    assert set(artifact.keys()) == {"estimator", "feature_columns", "metadata"}
    assert artifact["feature_columns"] == SAFE_MODEL_FEATURE_COLUMNS
    assert artifact["metadata"]["feature_columns"] == SAFE_MODEL_FEATURE_COLUMNS
    assert artifact["metadata"]["model_type"] == "logistic_regression"
    assert 0.2 <= artifact["metadata"]["threshold"] <= 0.8
    assert "pr_auc" in artifact["metadata"]["metrics"]
    assert artifact["metadata"]["selection_strategy"] == "balanced_f1_with_recall_floor"
    assert artifact["metadata"]["selection_score"] is not None
    assert artifact["metadata"]["threshold_strategy"] == "balanced_f1_with_recall_floor"
    assert artifact["metadata"]["threshold_metrics"]["threshold"] == artifact["metadata"]["threshold"]
    assert artifact["metadata"]["threshold_candidates_top_5"]
    assert artifact["metadata"]["dataset_id"] == 123
    assert artifact["metadata"]["random_state"] == 42
    assert artifact["metadata"]["sklearn_version"]
    assert result["metadata_path"] == str(metadata_path)
    assert result["best_model_name"] == "Logistic Regression"
    assert result["selection_strategy"] == "balanced_f1_with_recall_floor"
    assert result["selected_threshold"] == result["threshold"]
    assert result["threshold_metrics"]["threshold"] == result["threshold"]
    assert result["threshold_candidates_top_5"]
    assert "pr_auc" in result["metrics"]
    assert "feature_columns" in metadata_path.text
    assert runs and runs[0]["confusion_matrix_json"]
    assert runs[0]["pr_auc"] is not None
    assert 0.2 <= runs[0]["threshold"] <= 0.8


def test_auc_metrics_are_none_for_single_class_without_crash():
    metrics = ml_training_service._classification_metrics([1, 1, 1], [0.2, 0.7, 0.9], 0.5)

    assert metrics["roc_auc"] is None
    assert metrics["pr_auc"] is None
    assert metrics["confusion_matrix"]["tp"] == 2


def test_balanced_threshold_strategy_prefers_precision_guardrail():
    y_true = [1] * 10 + [0] * 10
    probabilities = [
        0.95,
        0.90,
        0.85,
        0.80,
        0.75,
        0.70,
        0.65,
        0.60,
        0.55,
        0.50,
        0.78,
        0.76,
        0.74,
        0.30,
        0.28,
        0.26,
        0.24,
        0.22,
        0.21,
        0.20,
    ]

    tuning = ml_training_service._tune_threshold(
        y_true,
        probabilities,
        "balanced_f1_with_recall_floor",
        target_recall=0.8,
    )
    selected = tuning["selected"]

    assert 0.2 <= selected["threshold"] <= 0.8
    assert selected["recall"] >= 0.8
    assert selected["precision"] >= 0.70
    assert selected["false_positive_count"] <= 3
    assert tuning["threshold_candidates_top_5"]
    assert "reason_for_selection" in tuning

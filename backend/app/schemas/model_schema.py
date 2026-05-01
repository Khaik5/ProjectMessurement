from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TrainingRequest(BaseModel):
    project_id: int = 1
    dataset_id: int | None = None
    model_type: Literal["all", "logistic_regression", "random_forest", "neural_network"] | None = None
    model_types: list[Literal["logistic_regression", "random_forest", "neural_network"]] | None = None
    auto_activate_best: bool = True
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    random_state: int = 42
    hidden_layer_size: int = Field(default=64, ge=8, le=512)
    max_iter: int = Field(default=500, ge=100, le=3000)
    threshold_strategy: Literal[
        "best_f1",
        "recall_weighted",
        "min_recall",
        "balanced_f1_with_recall_floor",
    ] = "balanced_f1_with_recall_floor"
    best_model_strategy: Literal["best_f1", "recall_weighted", "balanced_f1_with_recall_floor"] = "balanced_f1_with_recall_floor"
    target_recall: float = Field(default=0.8, ge=0.0, le=1.0)


class MLModelRead(BaseModel):
    id: int
    name: str
    model_type: str
    version: str
    artifact_path: str
    is_active: bool
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    roc_auc: float | None = None
    pr_auc: float | None = None
    threshold: float | None = None
    selection_strategy: str | None = None
    selection_score: float | None = None
    latency_ms: float | None = None
    hyperparameters_json: str | None = None
    created_at: datetime

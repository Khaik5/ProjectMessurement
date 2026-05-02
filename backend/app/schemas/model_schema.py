from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ModelKey = Literal["logistic_regression", "random_forest", "neural_network"]
TrainingProfile = Literal[
    "balanced_production",
    "high_recall",
    "high_precision",
    "best_roc_auc",
    "best_pr_auc",
    "custom",
]
ThresholdStrategy = Literal[
    "balanced_f1_with_recall_floor",
    "recall_priority",
    "precision_priority",
    "best_f1",
    "custom",
]
BestModelMetric = Literal["f1", "fbeta", "roc_auc", "pr_auc", "balanced_score", "precision", "recall_weighted", "precision_weighted"]


class ThresholdConfig(BaseModel):
    strategy: ThresholdStrategy | None = None
    recall_floor: float | None = Field(default=None, ge=0.0, le=1.0)
    precision_floor: float | None = Field(default=None, ge=0.0, le=1.0)
    beta: float | None = Field(default=None, gt=0.0, le=5.0)
    threshold_min: float | None = Field(default=None, ge=0.2, le=0.8)
    threshold_max: float | None = Field(default=None, ge=0.2, le=0.8)
    threshold_step: float | None = Field(default=None, gt=0.0, le=0.2)
    best_model_metric: BestModelMetric | None = None

    @field_validator("threshold_max")
    @classmethod
    def validate_threshold_range(cls, value, info):
        threshold_min = info.data.get("threshold_min")
        if value is not None and threshold_min is not None and value < threshold_min:
            raise ValueError("threshold_max must be >= threshold_min")
        return value


class TrainingRequest(BaseModel):
    project_id: int = 1
    dataset_id: int | None = None
    model_type: Literal["all", "logistic_regression", "random_forest", "neural_network"] | None = None
    model_types: list[ModelKey] | None = None
    selected_models: list[ModelKey] | None = None
    training_profile: TrainingProfile = "balanced_production"
    auto_activate_best: bool = True
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    random_state: int = 42
    hidden_layer_size: int = Field(default=64, ge=8, le=512)
    max_iter: int = Field(default=1000, ge=100, le=3000)
    threshold_strategy: Literal[
        "best_f1",
        "recall_weighted",
        "min_recall",
        "balanced_f1_with_recall_floor",
        "recall_priority",
        "precision_priority",
        "custom",
    ] | None = None
    best_model_strategy: Literal[
        "best_f1",
        "recall_weighted",
        "balanced_f1_with_recall_floor",
        "recall_priority",
        "precision_priority",
        "best_roc_auc",
        "best_pr_auc",
    ] | None = None
    target_recall: float = Field(default=0.8, ge=0.0, le=1.0)
    threshold_config: ThresholdConfig | None = None
    model_hyperparams: dict[str, dict] = Field(default_factory=dict)

    @field_validator("selected_models", "model_types")
    @classmethod
    def validate_unique_models(cls, value):
        if value and len(set(value)) != len(value):
            raise ValueError("selected models must be unique")
        return value


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
    training_profile: str | None = None
    metadata_path: str | None = None
    metrics_json: str | None = None
    is_best: bool | None = None
    status: str | None = None
    error_message: str | None = None
    latency_ms: float | None = None
    hyperparameters_json: str | None = None
    created_at: datetime

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MLModel:
    id: int
    name: str
    model_type: str
    version: str
    artifact_path: str
    is_active: bool
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    roc_auc: float | None
    latency_ms: float | None
    hyperparameters_json: str | None
    created_at: datetime

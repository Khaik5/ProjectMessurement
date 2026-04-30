from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrainingRun:
    id: int
    model_id: int | None
    dataset_id: int | None
    model_type: str
    model_version: str
    status: str
    train_size: int
    test_size: int
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    roc_auc: float | None
    confusion_matrix_json: str | None
    training_time_seconds: float | None
    parameters_json: str | None
    started_at: datetime
    completed_at: datetime | None

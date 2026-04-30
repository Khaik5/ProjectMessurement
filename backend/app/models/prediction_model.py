from dataclasses import dataclass
from datetime import datetime


@dataclass
class Prediction:
    id: int
    project_id: int
    dataset_id: int | None
    model_id: int | None
    module_name: str
    loc: int
    complexity: float
    coupling: float
    code_churn: float
    defect_probability: float
    prediction: int
    risk_level_id: int
    suggested_action: str
    created_at: datetime

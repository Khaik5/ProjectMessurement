from dataclasses import dataclass
from datetime import datetime


@dataclass
class MetricRecord:
    id: int
    dataset_id: int
    project_id: int
    module_id: int | None
    module_name: str
    loc: int
    complexity: float
    coupling: float
    code_churn: float
    defect_label: int | None
    recorded_at: datetime

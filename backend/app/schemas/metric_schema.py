from datetime import datetime

from pydantic import BaseModel, Field


class MetricRecordCreate(BaseModel):
    dataset_id: int
    project_id: int = 1
    module_name: str
    loc: int = Field(ge=0)
    complexity: float = Field(ge=0)
    coupling: float = Field(ge=0)
    code_churn: float = Field(ge=0)
    defect_label: int | None = None


class MetricRecordRead(MetricRecordCreate):
    id: int
    module_id: int | None = None
    recorded_at: datetime

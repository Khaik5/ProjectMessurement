from datetime import datetime

from pydantic import BaseModel, Field


class PredictionSingleRequest(BaseModel):
    project_id: int = 1
    module_name: str
    loc: int = Field(ge=0)
    complexity: float = Field(ge=0)
    coupling: float = Field(ge=0)
    code_churn: float = Field(ge=0)
    model_id: int | None = None


class PredictionRunRequest(BaseModel):
    project_id: int = 1
    dataset_id: int
    model_id: int | None = None


class PredictionRead(BaseModel):
    id: int | None = None
    module_name: str
    loc: int
    complexity: float
    coupling: float
    code_churn: float
    defect_probability: float
    prediction: int
    risk_level: str
    suggested_action: str
    model_source: str
    created_at: datetime

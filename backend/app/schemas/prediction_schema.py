from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PredictionSingleRequest(BaseModel):
    project_id: int = 1
    module_name: str
    loc: int = Field(ge=0)
    ncloc: int | None = Field(default=None, ge=0)
    cloc: int | None = Field(default=None, ge=0)
    complexity: float = Field(ge=0)
    cyclomatic_complexity: float | None = Field(default=None, ge=0)
    depth_of_nesting: float | None = Field(default=None, ge=0)
    coupling: float = Field(ge=0)
    cohesion: float | None = Field(default=None, ge=0)
    information_flow_complexity: float | None = Field(default=None, ge=0)
    code_churn: float = Field(ge=0)
    change_request_backlog: float | None = Field(default=None, ge=0)
    pending_effort_hours: float | None = Field(default=None, ge=0)
    percent_reused: float | None = Field(default=None, ge=0)
    model_id: int | None = None

    @field_validator("cohesion", "percent_reused")
    @classmethod
    def validate_ratio_or_percent(cls, value):
        if value is None:
            return value
        if value > 100:
            raise ValueError("must be in [0,1] or [0,100]")
        return value


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
    prediction_label: str | None = None
    risk_score: float | None = None
    risk_level: str
    suggested_action: str
    model_source: str
    used_fallback: bool | None = None
    created_at: datetime

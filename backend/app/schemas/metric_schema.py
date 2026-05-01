from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MetricRecordCreate(BaseModel):
    dataset_id: int
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
    defect_count: float | None = Field(default=None, ge=0)
    defect_label: int | None = None

    @field_validator("cohesion", "percent_reused")
    @classmethod
    def validate_ratio_or_percent(cls, value):
        if value is None:
            return value
        if value > 100:
            raise ValueError("must be in [0,1] or [0,100]")
        return value

    @field_validator("defect_label")
    @classmethod
    def validate_defect_label(cls, value):
        if value is None:
            return value
        if value not in (0, 1):
            raise ValueError("defect_label must be 0 or 1")
        return value


class MetricRecordRead(MetricRecordCreate):
    id: int
    module_id: int | None = None
    recorded_at: datetime

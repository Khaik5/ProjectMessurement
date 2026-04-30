from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    owner_id: int | None = 1


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    owner_id: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProjectStateUpdate(BaseModel):
    current_dataset_id: int | None = None
    current_model_id: int | None = None
    current_analysis_dataset_id: int | None = None

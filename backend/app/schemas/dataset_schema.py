from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DatasetRead(BaseModel):
    id: int
    project_id: int
    name: str
    file_name: str
    file_type: str
    row_count: int
    uploaded_by_id: int | None = None
    status: str
    validation_errors: str | None = None
    metadata_json: str | None = None
    uploaded_at: datetime


class DatasetUploadResponse(BaseModel):
    dataset: dict[str, Any]
    validation: dict[str, Any]
    preview: list[dict[str, Any]]


class DatasetPreview(BaseModel):
    dataset_id: int
    total_rows: int
    rows: list[dict[str, Any]]

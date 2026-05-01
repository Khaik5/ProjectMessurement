from datetime import datetime

from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    project_id: int = 1
    dataset_id: int | None = None
    generated_by_id: int | None = 1
    title: str = "DefectAI Software Defect Analysis"
    risk_level: str | None = None
    model_id: int | None = None
    days: int | None = 30


class ReportRead(BaseModel):
    id: int
    project_id: int
    generated_by_id: int | None
    title: str
    filters_json: str | None
    summary_json: str | None
    file_path: str | None
    created_at: datetime


class ExportMultipleReportsRequest(BaseModel):
    """Schema cho việc export nhiều reports cùng lúc"""
    report_ids: list[int]
    format: str = "csv"  # csv, pdf, xlsx

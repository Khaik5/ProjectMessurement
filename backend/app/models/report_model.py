from dataclasses import dataclass
from datetime import datetime


@dataclass
class Report:
    id: int
    project_id: int
    generated_by_id: int | None
    title: str
    filters_json: str | None
    summary_json: str | None
    file_path: str | None
    created_at: datetime

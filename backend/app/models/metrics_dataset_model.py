from dataclasses import dataclass
from datetime import datetime


@dataclass
class MetricsDataset:
    id: int
    project_id: int
    name: str
    file_name: str
    file_type: str
    row_count: int
    uploaded_by_id: int | None
    status: str
    validation_errors: str | None
    metadata_json: str | None
    uploaded_at: datetime

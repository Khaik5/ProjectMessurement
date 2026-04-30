from dataclasses import dataclass
from datetime import datetime


@dataclass
class CodeModule:
    id: int
    project_id: int
    module_name: str
    module_path: str | None
    language: str | None
    created_at: datetime

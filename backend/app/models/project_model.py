from dataclasses import dataclass
from datetime import datetime


@dataclass
class Project:
    id: int
    name: str
    description: str | None
    owner_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

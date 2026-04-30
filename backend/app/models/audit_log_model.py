from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuditLog:
    id: int
    user_id: int | None
    project_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    details_json: str | None
    ip_address: str | None
    created_at: datetime

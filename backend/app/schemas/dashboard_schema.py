from typing import Any

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    kpis: dict[str, Any]
    active_model: dict[str, Any] | None
    database_status: dict[str, Any]

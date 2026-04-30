from datetime import datetime

from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

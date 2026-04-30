from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    role: str
    is_active: bool
    created_at: datetime

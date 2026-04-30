from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=6, max_length=255)
    role: str = Field(default="Viewer", max_length=50)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=255)
    role: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class TokenPayload(BaseModel):
    sub: str
    user_id: int
    username: str
    roles: list[str] = []
    permissions: list[str] = []


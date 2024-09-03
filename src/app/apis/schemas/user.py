from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    is_enabled: bool
    last_login: datetime | None
    is_superuser: bool


class ShowUser(BaseModel):
    id: UUID
    username: str
    is_enabled: bool
    last_login: datetime | None
    is_superuser: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: str
    password: str
    is_enabled: bool
    is_superuser: bool

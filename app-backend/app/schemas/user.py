import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    is_allowed: bool = True
    role: UserRole = UserRole.driver


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    is_allowed: bool | None = None
    role: UserRole | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    is_allowed: bool
    role: UserRole
    created_at: datetime

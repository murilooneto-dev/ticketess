from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole
from app.schemas.common import EmailField, UsernameField


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    username: UsernameField
    email: EmailField | None = None
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.OPERADOR


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    username: UsernameField | None = None
    email: EmailField | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    email: EmailField | None
    role: UserRole
    is_active: bool
    created_at: datetime

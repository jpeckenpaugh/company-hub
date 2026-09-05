"""Pydantic serializers for the fastapi-users wiring.

``UserRead`` exposes exactly the contracted ``me`` payload
(``{id, email, is_superuser}``); ``UserCreate`` is the superuser-only account
creation body; ``UserUpdate`` limits self-service profile updates to the
password.

Email is carried as ``str`` (not Pydantic ``EmailStr``) because the bootstrap
admin address ``admin@localhost`` has a dot-less domain that ``email-validator``
rejects; a light shape check (non-empty, contains ``@``) replaces it.
"""

from fastapi_users.schemas import BaseUserCreate, CreateUpdateDictModel
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value:
        raise ValueError("must be a valid email address")
    return value


class UserRead(BaseModel):
    id: int
    email: str
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(CreateUpdateDictModel):
    password: str | None = None


class UserCreate(BaseUserCreate):
    email: str
    password: str = Field(min_length=8)
    is_active: bool | None = True
    is_superuser: bool | None = False
    is_verified: bool | None = True

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        return _validate_email(v)

    def create_update_dict_superuser(self) -> dict:
        return {
            "email": self.email,
            "password": self.password,
            "is_active": True if self.is_active is None else self.is_active,
            "is_superuser": False if self.is_superuser is None else self.is_superuser,
            "is_verified": True if self.is_verified is None else self.is_verified,
        }


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        return _validate_email(v)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
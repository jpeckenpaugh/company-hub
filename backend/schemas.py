"""Pydantic request models for the API contract.

All structured company fields are optional except ``name``, which is required
and must be non-empty.
"""

from typing import Optional

from pydantic import BaseModel, field_validator


class CompanyIn(BaseModel):
    name: str
    industry: Optional[str] = None
    hq_location: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InstitutionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    domain: str | None = Field(default=None, max_length=255)
    is_demo: bool = False
    is_active: bool = True
    settings: dict = Field(default_factory=dict)


class InstitutionCreate(InstitutionBase):
    pass


class InstitutionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    domain: str | None = Field(default=None, max_length=255)
    is_demo: bool | None = None
    is_active: bool | None = None
    settings: dict | None = None


class InstitutionResponse(InstitutionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    approved_at: datetime | None = None
    approved_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    institution_id: UUID | None = None
    profile_data: dict = Field(default_factory=dict)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=8)
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    profile_data: dict | None = None


class UserResponse(BaseModel):
    """
    Public and internal user profile response.
    CRITICAL SECURITY INVARIANT:
    Student-facing and User schemas NEVER contain cognitive analytics fields:
    (iori, hmm_probabilities, alpha_post, beta_post, mentor_notes, or referral_data).
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID | None
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    profile_data: dict = Field(default_factory=dict)


class UserBulkImportResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_records: int
    created_count: int
    failed_count: int
    errors: list[str] = Field(default_factory=list)

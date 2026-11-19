from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., description="Registered user email address")
    password: str = Field(..., description="User secret password")


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Access token expiration window in seconds")
    refresh_token: str | None = Field(default=None, description="Client refresh token if returned in response")
    user: UserResponse | None = Field(default=None, description="Authenticated user profile")


class RefreshRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Optional because it can also be retrieved securely from HttpOnly cookie
    refresh_token: str | None = Field(default=None, description="Client refresh token if not in cookie")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., description="Valid institutional email address")
    password: str = Field(..., min_length=6, description="Password meeting minimum security criteria")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full display name")
    institution_id: UUID | None = Field(
        default=None, description="Tenant institution identifier. Optional for auto-assignment."
    )
    role: UserRole = Field(
        default=UserRole.STUDENT,
        description="Assigned role: platform_admin, inst_admin, teacher, student",
    )

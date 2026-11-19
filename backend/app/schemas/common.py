from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SuccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True)
    message: str = Field(default="Operation completed successfully.")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False)
    detail: str = Field(..., description="Description of the error condition")
    code: str | None = Field(default=None, description="Internal error code")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

"""
Pydantic Schemas for Calendar Events
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CalendarEventCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    event_type: str = Field(default="university_event")
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    student_id: Optional[UUID] = None


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    student_id: UUID
    event_type: str
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    source_task_id: Optional[UUID] = None
    is_revised: bool
    original_datetime: Optional[datetime] = None
    created_at: datetime

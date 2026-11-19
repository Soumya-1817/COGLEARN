"""
Pydantic Schemas for Student Activity Events & Aggregates
"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ActivityEventCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_type: str = Field(..., description="navigate, open_resource, watch_video, read_pdf, take_notes, attempt_quiz, complete_assignment, prepare_project, submit_assessment, login, logout, download")
    course_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    event_data: dict[str, Any] = Field(default_factory=dict)
    occurred_at: Optional[datetime] = None


class ActivityEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    student_id: UUID
    course_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    event_type: str
    event_data: dict[str, Any]
    occurred_at: datetime
    session_id: Optional[UUID] = None
    is_anomalous: bool
    anomaly_reason: Optional[str] = None


class DailyAggregateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    student_id: UUID
    date: date
    total_clicks: int
    weighted_clicks: float
    valid_click_count: int
    anomalous_click_count: int
    session_count: int
    unique_courses_accessed: int

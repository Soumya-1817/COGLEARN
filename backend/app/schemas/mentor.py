"""
Pydantic Schemas for Mentor Intervention Engine
Note: Strictly restricted to mentors / teachers / admins.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InterventionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: UUID
    trigger_type: str = Field(default="manual", description="manual, iori_threshold, student_request")
    iori_value: Optional[float] = None
    risk_zone: Optional[str] = None


class InterventionClose(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    summary_notes: str = Field(..., min_length=3)


class InterventionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    mentor_id: UUID
    student_id: UUID
    trigger_type: str
    iori_value_at_trigger: Optional[float] = None
    risk_zone_at_trigger: Optional[str] = None
    status: str
    summary_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None


class MentorMessageCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    recipient_id: UUID
    body: str = Field(..., min_length=1)


class MentorMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    intervention_id: UUID
    sender_id: UUID
    recipient_id: UUID
    body: str
    sent_at: datetime
    is_read: bool


class MentorshipRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    student_id: UUID
    mentor_id: Optional[UUID] = None
    message: str
    status: str
    created_at: datetime
    intervention_id: Optional[str] = None


class MentalHealthReferralCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: UUID
    referral_body: str = Field(..., min_length=10)
    consent_recorded: bool = Field(..., description="Explicit student consent confirmation")


class MentalHealthReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    student_id: UUID
    referred_by_mentor_id: UUID
    status: str
    consent_recorded_at: Optional[datetime] = None
    created_at: datetime


class MentorStudentAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: str
    workload_breakdown: dict[str, float]
    iori_history: list[dict[str, Any]]
    latest_queue_metrics: Optional[dict[str, Any]] = None
    pending_tasks: list[dict[str, Any]]

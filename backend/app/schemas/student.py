"""
Pydantic Schemas for Student-Facing Endpoints
============================================
CRITICAL PRIVACY PRINCIPLE:
Student-facing schemas must NEVER include internal cognitive inference data:
NO iori, NO hmm_probabilities, NO alpha_post, NO beta_post,
NO capacity_estimate, NO mentor_notes, NO referral_data.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: Optional[UUID] = None
    email: str
    full_name: str
    role: str
    created_at: datetime


class StudentCourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: Optional[str] = None
    semester_id: Optional[UUID] = None
    department_id: Optional[UUID] = None


class StudentWorkloadSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    incoming_tasks: int
    overdue_tasks: int
    completed_tasks: int
    next_deadline: Optional[datetime] = None


class StudentTaskHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    course_id: UUID
    title: str
    task_type: str
    status: str
    due_date: datetime
    completion_timestamp: Optional[datetime] = None


class StudentCourseProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    course_id: UUID
    total_tasks: int
    completed_tasks: int
    completion_percentage: float


class MentorshipRequestCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message: str = Field(..., min_length=5, description="Brief explanation of the support requested")


class StudentMentorshipRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    message: str
    status: str
    created_at: datetime

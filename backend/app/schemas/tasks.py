"""
Pydantic Schemas for Academic Task Queue
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TaskStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str = Field(..., description="active, completed, pending")
    reason: Optional[str] = None


class AcademicTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    student_id: UUID
    course_id: UUID
    module_id: Optional[UUID] = None
    task_type: str
    source_id: UUID
    title: str
    description: Optional[str] = None
    arrival_timestamp: datetime
    queue_position: int
    due_date: datetime
    estimated_workload: float
    workload_weight: float  # PROVISIONAL
    status: str
    completion_timestamp: Optional[datetime] = None
    submission_id: Optional[UUID] = None
    is_overdue: Optional[bool] = False


class DeadlineExtensionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: UUID
    new_due_date: datetime
    reason: str = Field(..., min_length=3)


class DeadlineExtensionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    task_id: UUID
    student_id: UUID
    original_due_date: datetime
    new_due_date: datetime
    granted_by_mentor_id: UUID
    reason: str
    created_at: datetime

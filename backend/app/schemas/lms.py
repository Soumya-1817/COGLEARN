"""
Pydantic Schemas for LMS Core Entities
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# --- Department Schemas ---
class DepartmentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    name: str
    code: str
    description: Optional[str] = None
    created_at: datetime


# --- Programme Schemas ---
class ProgrammeCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    department_id: UUID
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None


class ProgrammeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    department_id: UUID
    name: str
    code: str
    description: Optional[str] = None
    created_at: datetime


# --- Semester Schemas ---
class SemesterCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., max_length=100)
    code: Optional[str] = Field(default=None, max_length=50)
    start_date: date
    end_date: date


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    name: str
    code: str
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime


# --- Course Schemas ---
class CourseCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    department_id: UUID
    semester_id: UUID
    teacher_id: Optional[UUID] = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    title: str
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    semester_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    is_published: bool
    created_at: datetime


class CourseEnrolRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: UUID


class EnrolmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    course_id: UUID
    student_id: UUID
    status: str
    enrolled_at: datetime


# --- Module Schemas ---
class ModuleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    order_index: int = 0


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    course_id: UUID
    title: str
    description: Optional[str] = None
    order_index: int
    created_at: datetime


# --- Lesson Schemas ---
class LessonCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    module_id: UUID
    title: str = Field(..., max_length=255)
    lesson_type: str = Field(default="video")
    content_url: Optional[str] = None
    duration_minutes: int = 0


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    course_id: UUID
    module_id: UUID
    title: str
    lesson_type: str
    content_url: Optional[str] = None
    duration_minutes: int
    order_index: int
    is_published: bool
    created_at: datetime


# --- Assignment Schemas ---
class AssignmentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: datetime
    estimated_hours: float = 1.0
    workload_weight: float = 1.5  # PROVISIONAL
    module_id: Optional[UUID] = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    course_id: UUID
    module_id: Optional[UUID] = None
    teacher_id: UUID
    title: str
    description: Optional[str] = None
    due_date: datetime
    estimated_hours: float
    workload_weight: float  # PROVISIONAL
    is_published: bool
    created_at: datetime


# --- Quiz Schemas ---
class QuizCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: datetime
    workload_weight: float = 1.2  # PROVISIONAL
    questions: list = Field(default_factory=list)
    time_limit_minutes: Optional[int] = None
    module_id: Optional[UUID] = None


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    course_id: UUID
    module_id: Optional[UUID] = None
    teacher_id: UUID
    title: str
    description: Optional[str] = None
    due_date: datetime
    time_limit_minutes: Optional[int] = None
    workload_weight: float  # PROVISIONAL
    questions: list
    is_published: bool
    created_at: datetime


# --- Assessment Schemas ---
class AssessmentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    assessment_type: str = Field(..., description="midterm, final, project, presentation")
    scheduled_date: datetime
    workload_weight: float = 2.0  # PROVISIONAL


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    course_id: UUID
    teacher_id: UUID
    title: str
    description: Optional[str] = None
    assessment_type: str
    scheduled_date: datetime
    workload_weight: float  # PROVISIONAL
    is_published: bool
    created_at: datetime


# --- Submission Schemas ---
class SubmissionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    content_text: Optional[str] = None
    content_url: Optional[str] = None


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    assignment_id: Optional[UUID] = None
    student_id: UUID
    submitted_at: datetime
    content_text: Optional[str] = None
    content_url: Optional[str] = None
    status: str

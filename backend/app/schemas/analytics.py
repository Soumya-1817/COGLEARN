"""
Pydantic Schemas for Institutional Analytics
"""

from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DepartmentAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    department_id: Optional[str] = None
    semester_id: Optional[str] = None
    student_count: int
    suppressed: bool
    message: Optional[str] = None
    avg_iori: Optional[float] = None
    iori_distribution: Optional[dict[str, int]] = None
    intervention_count: Optional[int] = None
    avg_workload: Optional[float] = None
    overdue_rate: Optional[float] = None


class ProgrammeAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    programme_id: Optional[str] = None
    department_id: Optional[str] = None
    semester_id: Optional[str] = None
    student_count: int
    suppressed: bool
    message: Optional[str] = None
    avg_iori: Optional[float] = None
    iori_distribution: Optional[dict[str, int]] = None
    intervention_count: Optional[int] = None
    avg_workload: Optional[float] = None
    overdue_rate: Optional[float] = None


class CourseAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    course_id: str
    student_count: int
    suppressed: bool
    message: Optional[str] = None
    submission_rate: Optional[float] = None
    completed_tasks: Optional[int] = None
    total_tasks: Optional[int] = None
    intervention_count: Optional[int] = None
    extension_count: Optional[int] = None
    avg_iori: Optional[float] = None


class InstitutionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_students: int
    total_teachers: int
    total_courses: int
    active_semester: Optional[str] = None
    avg_iori: float
    iori_distribution: dict[str, int]
    total_interventions: int
    active_interventions: int
    mentorship_coverage_rate: float

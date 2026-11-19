"""
Admin Institutional Analytics API Router
========================================
Endpoints for university administrators to review aggregate cognitive analytics,
curriculum health, and risk distributions.
Enforces k-anonymity privacy protections (suppresses cohort < MIN_COHORT_SIZE).
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.analytics import (
    CourseAnalyticsResponse,
    DepartmentAnalyticsResponse,
    InstitutionSummaryResponse,
    ProgrammeAnalyticsResponse,
)
from app.services import analytics_service

router = APIRouter(
    dependencies=[Depends(require_role(UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))]
)


@router.get("/admin/analytics/summary", response_model=InstitutionSummaryResponse)
async def get_institution_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Top-level institutional summary of student risk distribution,
    active courses, and intervention coverage.
    """
    return await analytics_service.get_institution_summary(
        db=db,
        institution_id=current_user.institution_id,
    )


@router.get("/admin/analytics/departments", response_model=DepartmentAnalyticsResponse)
async def get_department_analytics(
    department_id: Optional[UUID] = None,
    semester_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Department-level aggregate cognitive analytics and workload indicators.
    """
    return await analytics_service.get_department_analytics(
        db=db,
        institution_id=current_user.institution_id,
        department_id=department_id,
        semester_id=semester_id,
    )


@router.get("/admin/analytics/programmes", response_model=ProgrammeAnalyticsResponse)
async def get_programme_analytics(
    programme_id: Optional[UUID] = None,
    semester_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Degree programme aggregate cognitive analytics.
    """
    return await analytics_service.get_programme_analytics(
        db=db,
        institution_id=current_user.institution_id,
        programme_id=programme_id,
        semester_id=semester_id,
    )


@router.get("/admin/analytics/courses/{id}", response_model=CourseAnalyticsResponse)
async def get_course_analytics(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Course-level aggregate workload, completion rate, and cognitive load trend.
    """
    return await analytics_service.get_course_analytics(
        db=db,
        institution_id=current_user.institution_id,
        course_id=id,
    )

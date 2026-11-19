"""
Student Portal API Router
=========================
Endpoints for student profile access, course enrollments, and requesting mentorship.
Strict privacy governance enforced.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.course import Course
from app.models.enrolment import CourseEnrolment, EnrolmentStatus
from app.models.mentorship_request import MentorshipRequest
from app.models.user import User
from app.schemas.student import (
    MentorshipRequestCreate,
    StudentCourseSummary,
    StudentMentorshipRequestResponse,
    StudentProfileResponse,
)
from app.services import intervention_service, lms_service

router = APIRouter()


@router.get("/students/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns authenticated student's profile information.
    Excludes any internal risk tags or administrative annotations.
    """
    return StudentProfileResponse(
        id=current_user.id,
        institution_id=current_user.institution_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        created_at=current_user.created_at,
    )


@router.get("/students/me/courses", response_model=list[StudentCourseSummary])
async def get_my_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns active course enrolments for the authenticated student.
    """
    courses = await lms_service.get_student_courses(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
    )
    return [
        StudentCourseSummary(
            id=c["id"],
            title=c["title"],
            description=c.get("description"),
            semester_id=c.get("semester_id"),
            department_id=c.get("department_id"),
        )
        for c in courses
    ]


@router.post(
    "/students/me/request-mentorship",
    response_model=StudentMentorshipRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_mentorship(
    req_in: MentorshipRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Student-initiated request for academic mentorship or workload support.
    Completely independent of cognitive risk scores: any student may ask for guidance at any time.
    """
    req_dict = await intervention_service.create_mentorship_request(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
        message=req_in.message,
    )
    return StudentMentorshipRequestResponse(
        id=req_dict["id"],
        message=req_dict["message"],
        status=req_dict["status"],
        created_at=req_dict["created_at"],
    )


@router.get(
    "/students/me/mentorship-requests",
    response_model=list[StudentMentorshipRequestResponse],
)
async def get_my_mentorship_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List historical mentorship requests initiated by the student.
    """
    stmt = (
        select(MentorshipRequest)
        .where(
            and_(
                MentorshipRequest.student_id == current_user.id,
                MentorshipRequest.institution_id == current_user.institution_id,
            )
        )
        .order_by(MentorshipRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [
        StudentMentorshipRequestResponse(
            id=r.id,
            message=r.message,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            created_at=r.created_at,
        )
        for r in records
    ]

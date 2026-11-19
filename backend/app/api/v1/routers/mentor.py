"""
Mentor Intervention API Router
==============================
Authorized endpoints for teachers, mentors, and academic advisors.
Allows viewing authorized cognitive risk analytics (IORI), managing interventions,
granting deadline extensions, and student communications.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.course import Course
from app.models.enrolment import CourseEnrolment, EnrolmentStatus
from app.models.mentorship_request import MentorshipRequest, MentorshipRequestStatus
from app.models.user import User, UserRole
from app.schemas.mentor import (
    InterventionClose,
    InterventionCreate,
    InterventionResponse,
    MentalHealthReferralCreate,
    MentalHealthReferralResponse,
    MentorMessageCreate,
    MentorMessageResponse,
    MentorshipRequestResponse,
    MentorStudentAnalyticsResponse,
)
from app.schemas.tasks import DeadlineExtensionCreate, DeadlineExtensionResponse
from app.services import intervention_service, task_queue_service

router = APIRouter(
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))]
)


@router.get("/mentor/students", response_model=list[dict])
async def list_assigned_students(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all students assigned to this mentor or enrolled in courses taught by this teacher.
    """
    if current_user.role in (UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN):
        # Admins can see all students in tenant
        stmt = (
            select(User)
            .where(
                and_(
                    User.institution_id == current_user.institution_id,
                    User.role == UserRole.STUDENT,
                    User.is_active.is_(True),
                )
            )
            .order_by(User.full_name.asc())
        )
    else:
        # Teachers see students enrolled in their courses
        stmt = (
            select(User)
            .join(CourseEnrolment, CourseEnrolment.student_id == User.id)
            .join(Course, Course.id == CourseEnrolment.course_id)
            .where(
                and_(
                    Course.teacher_id == current_user.id,
                    Course.institution_id == current_user.institution_id,
                    CourseEnrolment.status == EnrolmentStatus.ENROLLED,
                    User.is_active.is_(True),
                )
            )
            .distinct()
            .order_by(User.full_name.asc())
        )

    result = await db.execute(stmt)
    students = result.scalars().all()
    out = []
    for s in students:
        out.append({
            "id": str(s.id),
            "full_name": s.full_name,
            "email": s.email,
            "role": s.role.value if hasattr(s.role, "value") else str(s.role),
            "created_at": s.created_at.isoformat(),
        })
    return out


@router.get("/mentor/students/{student_id}/analytics", response_model=MentorStudentAnalyticsResponse)
async def get_student_authorized_analytics(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authorized view of student analytics for mentors (includes IORI trend, M/M/1 queue metrics,
    and task breakdown).
    NEVER includes raw HMM transition probabilities or medical records.
    """
    try:
        return await intervention_service.get_mentor_student_analytics(
            db=db,
            institution_id=current_user.institution_id,
            mentor_id=current_user.id,
            student_id=student_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/mentor/interventions", response_model=list[InterventionResponse])
async def list_interventions(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all interventions handled by this mentor.
    """
    return await intervention_service.get_mentor_interventions(
        db=db,
        institution_id=current_user.institution_id,
        mentor_id=current_user.id,
        status=status,
    )


@router.post("/mentor/interventions", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
async def create_intervention(
    int_in: InterventionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Open an intervention for an at-risk student.
    """
    return await intervention_service.create_intervention(
        db=db,
        institution_id=current_user.institution_id,
        mentor_id=current_user.id,
        student_id=int_in.student_id,
        trigger_type=int_in.trigger_type,
        iori_value=int_in.iori_value,
        risk_zone=int_in.risk_zone,
    )


@router.get("/mentor/interventions/{id}/messages", response_model=list[MentorMessageResponse])
async def get_intervention_messages(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve message thread for an intervention.
    """
    try:
        return await intervention_service.get_intervention_messages(
            db=db,
            institution_id=current_user.institution_id,
            intervention_id=id,
            requesting_user_id=current_user.id,
        )
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/mentor/interventions/{id}/messages", response_model=MentorMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_intervention_message(
    id: UUID,
    msg_in: MentorMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message within an active intervention.
    """
    try:
        return await intervention_service.send_mentor_message(
            db=db,
            institution_id=current_user.institution_id,
            intervention_id=id,
            sender_id=current_user.id,
            recipient_id=msg_in.recipient_id,
            body=msg_in.body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/mentor/interventions/{id}/close", response_model=InterventionResponse)
async def close_intervention(
    id: UUID,
    close_in: InterventionClose,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Close an intervention with closing notes.
    """
    try:
        return await intervention_service.close_intervention(
            db=db,
            institution_id=current_user.institution_id,
            intervention_id=id,
            mentor_id=current_user.id,
            summary_notes=close_in.summary_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/mentor/requests", response_model=list[MentorshipRequestResponse])
async def list_mentorship_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List pending mentorship requests submitted by students.
    """
    stmt = (
        select(MentorshipRequest)
        .where(
            and_(
                MentorshipRequest.institution_id == current_user.institution_id,
                MentorshipRequest.status == MentorshipRequestStatus.PENDING,
            )
        )
        .order_by(MentorshipRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    reqs = result.scalars().all()
    return [intervention_service._model_to_dict(r) for r in reqs]


@router.post("/mentor/requests/{id}/accept", response_model=MentorshipRequestResponse)
async def accept_mentorship_request(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept student's mentorship request and initiate intervention.
    """
    try:
        return await intervention_service.accept_mentorship_request(
            db=db,
            institution_id=current_user.institution_id,
            request_id=id,
            mentor_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/mentor/extensions", response_model=DeadlineExtensionResponse, status_code=status.HTTP_201_CREATED)
async def grant_deadline_extension(
    ext_in: DeadlineExtensionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Grant an academic deadline extension for a task.
    Preserves original due date in audit log and updates calendar.
    """
    try:
        return await task_queue_service.extend_task_deadline(
            db=db,
            institution_id=current_user.institution_id,
            task_id=ext_in.task_id,
            new_due_date=ext_in.new_due_date,
            mentor_id=current_user.id,
            reason=ext_in.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/mentor/referrals", response_model=MentalHealthReferralResponse, status_code=status.HTTP_201_CREATED)
async def create_mental_health_referral(
    ref_in: MentalHealthReferralCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a mental health and counseling referral.
    RESTRICTED: Requires explicit recorded consent.
    """
    try:
        return await intervention_service.create_mental_health_referral(
            db=db,
            institution_id=current_user.institution_id,
            mentor_id=current_user.id,
            student_id=ref_in.student_id,
            referral_body=ref_in.referral_body,
            consent_recorded=ref_in.consent_recorded,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

"""
Student Self-Analytics API Router
=================================
Student-facing endpoints providing operational progress and workload status.

CRITICAL ARCHITECTURAL SAFEGUARD:
These endpoints MUST NEVER reveal internal cognitive risk metrics:
- NO IORI values or risk zones
- NO Hidden Markov Model probabilities
- NO Bayesian capacity estimates (alpha_post, beta_post, mu)
- NO mentor evaluation notes or mental health referrals
Only observable academic facts (tasks assigned, completed, upcoming deadlines)
are presented to prevent cognitive self-bias or performance anxiety.
"""

from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.academic_task import AcademicTask, AcademicTaskStatus
from app.models.user import User
from app.schemas.student import (
    StudentCourseProgressResponse,
    StudentTaskHistoryItem,
    StudentWorkloadSummaryResponse,
)

router = APIRouter()


@router.get("/my/analytics/workload-summary", response_model=StudentWorkloadSummaryResponse)
async def get_my_workload_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns student-facing workload counts: incoming, overdue, completed tasks,
    and the timestamp of the next upcoming deadline.
    Strictly excludes cognitive risk indices (IORI) and Bayesian capacity parameters.
    """
    now = datetime.now(timezone.utc)

    # 1. Incoming (active/pending due in the future)
    incoming_stmt = select(func.count(AcademicTask.id)).where(
        and_(
            AcademicTask.student_id == current_user.id,
            AcademicTask.institution_id == current_user.institution_id,
            AcademicTask.status.in_([AcademicTaskStatus.PENDING, AcademicTaskStatus.ACTIVE]),
            AcademicTask.due_date >= now,
        )
    )
    incoming_tasks = (await db.execute(incoming_stmt)).scalar() or 0

    # 2. Overdue
    overdue_stmt = select(func.count(AcademicTask.id)).where(
        and_(
            AcademicTask.student_id == current_user.id,
            AcademicTask.institution_id == current_user.institution_id,
            (
                (AcademicTask.status == AcademicTaskStatus.OVERDUE)
                | (
                    AcademicTask.status.in_([AcademicTaskStatus.PENDING, AcademicTaskStatus.ACTIVE])
                    & (AcademicTask.due_date < now)
                )
            ),
        )
    )
    overdue_tasks = (await db.execute(overdue_stmt)).scalar() or 0

    # 3. Completed
    completed_stmt = select(func.count(AcademicTask.id)).where(
        and_(
            AcademicTask.student_id == current_user.id,
            AcademicTask.institution_id == current_user.institution_id,
            AcademicTask.status == AcademicTaskStatus.COMPLETED,
        )
    )
    completed_tasks = (await db.execute(completed_stmt)).scalar() or 0

    # 4. Next upcoming deadline
    next_deadline_stmt = (
        select(AcademicTask.due_date)
        .where(
            and_(
                AcademicTask.student_id == current_user.id,
                AcademicTask.institution_id == current_user.institution_id,
                AcademicTask.status.in_([AcademicTaskStatus.PENDING, AcademicTaskStatus.ACTIVE]),
                AcademicTask.due_date >= now,
            )
        )
        .order_by(AcademicTask.due_date.asc())
        .limit(1)
    )
    next_deadline = (await db.execute(next_deadline_stmt)).scalar_one_or_none()

    return StudentWorkloadSummaryResponse(
        incoming_tasks=incoming_tasks,
        overdue_tasks=overdue_tasks,
        completed_tasks=completed_tasks,
        next_deadline=next_deadline,
    )


@router.get("/my/analytics/task-history", response_model=list[StudentTaskHistoryItem])
async def get_my_task_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns student's historical academic tasks with completion status.
    Excludes all mentor notes and internal risk calculations.
    """
    stmt = (
        select(AcademicTask)
        .where(
            and_(
                AcademicTask.student_id == current_user.id,
                AcademicTask.institution_id == current_user.institution_id,
            )
        )
        .order_by(AcademicTask.arrival_timestamp.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return [
        StudentTaskHistoryItem(
            id=t.id,
            course_id=t.course_id,
            title=t.title,
            task_type=t.task_type.value if hasattr(t.task_type, "value") else str(t.task_type),
            status=t.status.value if hasattr(t.status, "value") else str(t.status),
            due_date=t.due_date,
            completion_timestamp=t.completion_timestamp,
        )
        for t in tasks
    ]


@router.get("/my/progress/{course_id}", response_model=StudentCourseProgressResponse)
async def get_course_progress(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns completion progress percentage for a specific enrolled course.
    """
    total_stmt = select(func.count(AcademicTask.id)).where(
        and_(
            AcademicTask.student_id == current_user.id,
            AcademicTask.course_id == course_id,
            AcademicTask.institution_id == current_user.institution_id,
        )
    )
    total_tasks = (await db.execute(total_stmt)).scalar() or 0

    comp_stmt = select(func.count(AcademicTask.id)).where(
        and_(
            AcademicTask.student_id == current_user.id,
            AcademicTask.course_id == course_id,
            AcademicTask.institution_id == current_user.institution_id,
            AcademicTask.status == AcademicTaskStatus.COMPLETED,
        )
    )
    completed_tasks = (await db.execute(comp_stmt)).scalar() or 0

    pct = round((completed_tasks / total_tasks * 100.0), 1) if total_tasks > 0 else 0.0

    return StudentCourseProgressResponse(
        course_id=course_id,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_percentage=pct,
    )

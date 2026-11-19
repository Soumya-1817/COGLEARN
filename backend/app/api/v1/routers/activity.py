"""
Activity Telemetry API Router
=============================
Endpoints for student activity event capture, auditing, and daily aggregates.
"""

from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.activity_event import ActivityEvent
from app.models.user import User, UserRole
from app.schemas.activity import (
    ActivityEventCreate,
    ActivityEventResponse,
    DailyAggregateResponse,
)
from app.services import activity_service

router = APIRouter()


@router.post(
    "/activity/events",
    response_model=ActivityEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_activity(
    event_in: ActivityEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Records an activity telemetry event for the current authenticated student.
    Triggers ICAP weighted aggregation and anomaly protection checks.
    """
    return await activity_service.record_activity_event(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
        event_type=event_in.event_type,
        course_id=event_in.course_id,
        lesson_id=event_in.lesson_id,
        session_id=event_in.session_id,
        event_data=event_in.event_data,
        occurred_at=event_in.occurred_at,
    )


@router.get(
    "/activity/events",
    response_model=list[ActivityEventResponse],
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def list_activity_events(
    student_id: Optional[UUID] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List raw activity events for audit and investigation (Teachers/Admins only).
    """
    conditions = [ActivityEvent.institution_id == current_user.institution_id]
    if student_id:
        conditions.append(ActivityEvent.student_id == student_id)

    stmt = (
        select(ActivityEvent)
        .where(and_(*conditions))
        .order_by(ActivityEvent.occurred_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [activity_service._model_to_dict(r) for r in records]


@router.get(
    "/activity/daily-aggregate/{student_id}/{for_date}",
    response_model=DailyAggregateResponse,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def get_daily_aggregate(
    student_id: UUID,
    for_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves or calculates daily aggregate interaction metrics for a student.
    """
    try:
        return await activity_service.update_daily_aggregate(
            db=db,
            institution_id=current_user.institution_id,
            student_id=student_id,
            for_date=for_date,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

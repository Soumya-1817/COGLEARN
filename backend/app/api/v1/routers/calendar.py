"""
Calendar API Router
===================
Endpoints for student academic calendar schedules, upcoming deadlines,
and institutional events.
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.calendar import CalendarEventCreate, CalendarEventResponse
from app.services import calendar_service

router = APIRouter()


@router.get("/calendar", response_model=list[CalendarEventResponse])
async def get_student_calendar(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns calendar events for the student within a date window.
    Defaults to current month window.
    """
    today = date.today()
    s_date = start_date or today.replace(day=1)
    e_date = end_date or (today + timedelta(days=31))

    return await calendar_service.get_student_calendar(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
        start_date=s_date,
        end_date=e_date,
    )


@router.get("/calendar/upcoming", response_model=list[CalendarEventResponse])
async def get_upcoming_events(
    days: int = Query(default=7, ge=1, le=60),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns upcoming deadlines and milestones due within next N days.
    """
    return await calendar_service.get_upcoming_deadlines(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
        days_ahead=days,
    )


@router.post(
    "/calendar/events",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN, UserRole.TEACHER))],
)
async def create_calendar_event(
    event_in: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a university or course event (Admins and Teachers only).
    """
    target_student_id = event_in.student_id or current_user.id

    return await calendar_service.create_calendar_event(
        db=db,
        institution_id=current_user.institution_id,
        student_id=target_student_id,
        event_type=event_in.event_type,
        title=event_in.title,
        start_datetime=event_in.start_datetime,
        end_datetime=event_in.end_datetime,
        description=event_in.description,
    )

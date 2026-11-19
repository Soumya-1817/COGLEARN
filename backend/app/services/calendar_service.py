"""
Calendar Service
================
Manages student academic calendars.

Calendar events are automatically created when:
- Teacher publishes an assignment (creates 'assignment_due' event)
- Teacher publishes a quiz (creates 'quiz_due' event)
- Teacher publishes an assessment (creates 'assessment' event)
- University admin creates a university event

Deadline extensions update the existing calendar event:
- is_revised = True
- original_datetime is preserved
- start_datetime is updated to new_due_date

Reminder notifications are generated based on notification_preferences.
"""

from datetime import date, datetime, timedelta, timezone
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent, CalendarEventType

logger = logging.getLogger(__name__)


def _model_to_dict(model_instance: Any) -> dict[str, Any]:
    """Serializes a SQLAlchemy model instance into a dictionary."""
    if model_instance is None:
        return {}
    res = {}
    for column in model_instance.__table__.columns:
        val = getattr(model_instance, column.name)
        if isinstance(val, UUID):
            res[column.name] = str(val)
        elif isinstance(val, (datetime, date)):
            res[column.name] = val.isoformat()
        elif hasattr(val, "value"):
            res[column.name] = val.value
        else:
            res[column.name] = val
    return res


async def create_calendar_event(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    event_type: str,
    title: str,
    start_datetime: datetime,
    end_datetime: Optional[datetime] = None,
    description: Optional[str] = None,
    source_task_id: Optional[UUID] = None,
) -> dict:
    """Creates a calendar event for an individual student."""
    try:
        ev_type = CalendarEventType(event_type.lower())
    except ValueError:
        ev_type = CalendarEventType.UNIVERSITY_EVENT

    event = CalendarEvent(
        id=uuid4(),
        institution_id=institution_id,
        student_id=student_id,
        event_type=ev_type,
        title=title.strip(),
        description=description.strip() if description else None,
        start_datetime=start_datetime,
        end_datetime=end_datetime or start_datetime,
        source_task_id=source_task_id,
        is_revised=False,
        original_datetime=start_datetime,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return _model_to_dict(event)


async def bulk_create_calendar_events(
    db: AsyncSession,
    institution_id: UUID,
    student_ids: list[UUID],
    event_type: str,
    title: str,
    start_datetime: datetime,
    source_task_ids: Optional[dict[UUID, UUID]] = None,
) -> list[dict]:
    """Bulk creates calendar events for multiple students."""
    try:
        ev_type = CalendarEventType(event_type.lower())
    except ValueError:
        ev_type = CalendarEventType.UNIVERSITY_EVENT

    created_events = []
    for s_id in student_ids:
        task_id = source_task_ids.get(s_id) if source_task_ids else None
        event = CalendarEvent(
            id=uuid4(),
            institution_id=institution_id,
            student_id=s_id,
            event_type=ev_type,
            title=title.strip(),
            start_datetime=start_datetime,
            end_datetime=start_datetime,
            source_task_id=task_id,
            is_revised=False,
            original_datetime=start_datetime,
        )
        db.add(event)
        created_events.append(event)

    await db.commit()
    for ev in created_events:
        await db.refresh(ev)

    return [_model_to_dict(e) for e in created_events]


async def update_calendar_event_deadline(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    source_task_id: UUID,
    new_due_date: datetime,
) -> dict:
    """
    Update a calendar event when a deadline is extended.
    Preserves original_datetime. Sets is_revised = True.
    """
    stmt = select(CalendarEvent).where(
        and_(
            CalendarEvent.source_task_id == source_task_id,
            CalendarEvent.student_id == student_id,
            CalendarEvent.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if event is None:
        # Fallback: create a revised event
        return await create_calendar_event(
            db=db,
            institution_id=institution_id,
            student_id=student_id,
            event_type=CalendarEventType.ASSIGNMENT_DUE.value,
            title="Revised Deadline",
            start_datetime=new_due_date,
            source_task_id=source_task_id,
        )

    if not event.original_datetime:
        event.original_datetime = event.start_datetime

    event.start_datetime = new_due_date
    event.end_datetime = new_due_date
    event.is_revised = True
    event.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(event)
    return _model_to_dict(event)


async def get_student_calendar(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Retrieves all calendar events for a student within date bounds."""
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

    stmt = (
        select(CalendarEvent)
        .where(
            and_(
                CalendarEvent.student_id == student_id,
                CalendarEvent.institution_id == institution_id,
                CalendarEvent.start_datetime >= start_dt,
                CalendarEvent.start_datetime <= end_dt,
            )
        )
        .order_by(CalendarEvent.start_datetime.asc())
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    return [_model_to_dict(e) for e in events]


async def get_upcoming_deadlines(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    days_ahead: int = 7,
) -> list[dict]:
    """Retrieves upcoming assignment and assessment deadlines in next N days."""
    now = datetime.now(timezone.utc)
    future_limit = now + timedelta(days=days_ahead)

    stmt = (
        select(CalendarEvent)
        .where(
            and_(
                CalendarEvent.student_id == student_id,
                CalendarEvent.institution_id == institution_id,
                CalendarEvent.start_datetime >= now,
                CalendarEvent.start_datetime <= future_limit,
                CalendarEvent.event_type.in_(
                    [
                        CalendarEventType.ASSIGNMENT_DUE,
                        CalendarEventType.QUIZ_DUE,
                        CalendarEventType.ASSESSMENT,
                    ]
                ),
            )
        )
        .order_by(CalendarEvent.start_datetime.asc())
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    return [_model_to_dict(e) for e in events]

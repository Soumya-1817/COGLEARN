"""
Activity Event Service
======================
Captures, validates, and aggregates student learning interaction events.

Event types map to ICAP levels:
  navigate, open_resource, watch_video -> Passive
  read_pdf, take_notes, download -> Active  
  attempt_quiz, complete_assignment -> Constructive
  prepare_project, submit_assessment -> Interactive

Anomaly detection flags events where total daily clicks exceed
the z-score threshold or rapid bot-like click thresholds, to protect
the Bayesian capacity estimation model.
"""

from datetime import date, datetime, timezone
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.model3_workload import PROVISIONAL_WEIGHTS
from app.models.activity_event import ActivityEvent, ActivityEventType
from app.models.activity_weight_config import ActivityWeightConfig, ICAPLevel
from app.models.daily_activity_aggregate import DailyActivityAggregate

logger = logging.getLogger(__name__)

# Heuristic threshold for anomalous automated/scripted click activity
MAX_DAILY_CLICKS_THRESHOLD = 1500  # PROVISIONAL


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


async def get_activity_weight_config(
    db: AsyncSession,
    institution_id: UUID,
    as_of_date: Optional[date] = None,
) -> dict[str, float]:
    """
    Load the ICAP weight configuration active on `as_of_date`.
    Returns dict mapping event_type -> weight.
    Falls back to PROVISIONAL_WEIGHTS from model3_workload if no DB config.
    """
    check_date = as_of_date or date.today()

    stmt = select(ActivityWeightConfig).where(
        and_(
            ActivityWeightConfig.institution_id == institution_id,
            ActivityWeightConfig.effective_date <= check_date,
            (
                (ActivityWeightConfig.deprecated_at.is_(None))
                | (ActivityWeightConfig.deprecated_at > check_date)
            ),
        )
    )
    result = await db.execute(stmt)
    configs = result.scalars().all()

    if not configs:
        # Fallback to PROVISIONAL_WEIGHTS
        return dict(PROVISIONAL_WEIGHTS)  # PROVISIONAL

    weights: dict[str, float] = {}
    for cfg in configs:
        weights[cfg.activity_type] = cfg.weight
    return weights


async def record_activity_event(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    event_type: str,
    course_id: Optional[UUID] = None,
    lesson_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    event_data: Optional[dict] = None,
    occurred_at: Optional[datetime] = None,
) -> dict:
    """
    Record a single activity event and trigger daily aggregate update.
    Applies anomaly detection against high-volume click bursts.
    Returns the created event record.
    """
    timestamp = occurred_at or datetime.now(timezone.utc)
    event_date = timestamp.date()

    # Validate event_type against enum
    try:
        activity_type_enum = ActivityEventType(event_type.lower())
    except ValueError:
        activity_type_enum = ActivityEventType.NAVIGATE

    # Anomaly check: Count existing clicks for student today
    count_stmt = select(func.count(ActivityEvent.id)).where(
        and_(
            ActivityEvent.student_id == student_id,
            ActivityEvent.institution_id == institution_id,
            func.date(ActivityEvent.occurred_at) == event_date,
        )
    )
    clicks_today = (await db.execute(count_stmt)).scalar() or 0

    is_anomalous = False
    anomaly_reason: Optional[str] = None
    if clicks_today >= MAX_DAILY_CLICKS_THRESHOLD:
        is_anomalous = True
        anomaly_reason = f"Daily click volume exceeded threshold ({clicks_today} >= {MAX_DAILY_CLICKS_THRESHOLD})"

    event = ActivityEvent(
        id=uuid4(),
        institution_id=institution_id,
        student_id=student_id,
        course_id=course_id,
        lesson_id=lesson_id,
        session_id=session_id,
        event_type=activity_type_enum,
        event_data=event_data or {},
        occurred_at=timestamp,
        is_anomalous=is_anomalous,
        anomaly_reason=anomaly_reason,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Recalculate daily aggregate
    await update_daily_aggregate(db, institution_id, student_id, event_date)

    return _model_to_dict(event)


async def update_daily_aggregate(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    for_date: date,
) -> dict:
    """
    Recalculate the daily activity aggregate for a student on a given date.
    Uses the ICAP weight registry to compute weighted_clicks.
    Counts valid vs anomalous events.
    """
    # Load all events on that day
    stmt = select(ActivityEvent).where(
        and_(
            ActivityEvent.student_id == student_id,
            ActivityEvent.institution_id == institution_id,
            func.date(ActivityEvent.occurred_at) == for_date,
        )
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    total_clicks = len(events)
    valid_clicks = 0
    anomalous_clicks = 0
    sessions = set()
    courses = set()

    weights = await get_activity_weight_config(db, institution_id, as_of_date=for_date)
    weighted_clicks = 0.0

    for ev in events:
        if ev.is_anomalous:
            anomalous_clicks += 1
        else:
            valid_clicks += 1
            ev_type_str = ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type)
            w = weights.get(ev_type_str, 0.10)  # default PROVISIONAL weight
            weighted_clicks += float(w)

        if ev.session_id:
            sessions.add(ev.session_id)
        if ev.course_id:
            courses.add(ev.course_id)

    # Check if aggregate already exists
    agg_stmt = select(DailyActivityAggregate).where(
        and_(
            DailyActivityAggregate.student_id == student_id,
            DailyActivityAggregate.institution_id == institution_id,
            DailyActivityAggregate.date == for_date,
        )
    )
    existing_agg = (await db.execute(agg_stmt)).scalar_one_or_none()

    if existing_agg:
        existing_agg.total_clicks = total_clicks
        existing_agg.valid_click_count = valid_clicks
        existing_agg.anomalous_click_count = anomalous_clicks
        existing_agg.weighted_clicks = round(weighted_clicks, 4)
        existing_agg.session_count = len(sessions)
        existing_agg.unique_courses_accessed = len(courses)
        existing_agg.updated_at = datetime.now(timezone.utc)
        aggregate = existing_agg
    else:
        aggregate = DailyActivityAggregate(
            id=uuid4(),
            institution_id=institution_id,
            student_id=student_id,
            date=for_date,
            total_clicks=total_clicks,
            valid_click_count=valid_clicks,
            anomalous_click_count=anomalous_clicks,
            weighted_clicks=round(weighted_clicks, 4),
            session_count=len(sessions),
            unique_courses_accessed=len(courses),
        )
        db.add(aggregate)

    await db.commit()
    await db.refresh(aggregate)
    return _model_to_dict(aggregate)


async def get_daily_aggregates(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Retrieve daily aggregates for a student within a date range."""
    stmt = (
        select(DailyActivityAggregate)
        .where(
            and_(
                DailyActivityAggregate.student_id == student_id,
                DailyActivityAggregate.institution_id == institution_id,
                DailyActivityAggregate.date >= start_date,
                DailyActivityAggregate.date <= end_date,
            )
        )
        .order_by(DailyActivityAggregate.date.asc())
    )
    result = await db.execute(stmt)
    aggregates = result.scalars().all()
    return [_model_to_dict(a) for a in aggregates]

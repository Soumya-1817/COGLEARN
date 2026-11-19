"""
Notification Service
====================
Manages in-app notifications with pluggable email delivery.

Categories:
  academic_announcement, new_assignment, upcoming_deadline,
  assessment_reminder, mentor_message, deadline_extension,
  university_announcement, support_notification

Priority levels: low, medium, high, urgent

Miller 7+/-2 principle: notifications are grouped by category and
prioritized so the student is never overwhelmed with low-priority items.
This is a cognitive-load design guideline, not a hard restriction on
academic information access.

Delivery:
  1. In-app: stored in notifications table, pushed via WebSocket if connected
  2. Email: dispatched via SMTP (async Celery/worker or direct background task)
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.academic_task import AcademicTask, AcademicTaskStatus
from app.models.notification import Notification, NotificationCategory, NotificationPriority
from app.models.notification_preference import NotificationPreference
from app.models.user import User

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
        elif isinstance(val, datetime):
            res[column.name] = val.isoformat()
        elif hasattr(val, "value"):
            res[column.name] = val.value
        else:
            res[column.name] = val
    return res


async def _dispatch_email(
    to_email: str,
    subject: str,
    body: str,
) -> None:
    """Dispatches email notification asynchronously if SMTP settings are present."""
    if not settings.SMTP_HOST:
        logger.debug("SMTP host not configured. Skipping email dispatch to %s.", to_email)
        return

    try:
        import asyncio
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        def _send_sync():
            msg = MIMEMultipart()
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _send_sync)
    except Exception as exc:
        logger.warning("Failed to send email notification to %s: %s", to_email, exc)


async def create_notification(
    db: AsyncSession,
    institution_id: UUID,
    recipient_id: UUID,
    category: str,
    title: str,
    body: str,
    priority: str = "medium",
    action_url: Optional[str] = None,
    source_id: Optional[UUID] = None,
) -> dict:
    """
    Creates an in-app notification record and optionally dispatches email
    based on recipient preferences.
    """
    try:
        cat_enum = NotificationCategory(category.lower())
    except ValueError:
        cat_enum = NotificationCategory.ACADEMIC_ANNOUNCEMENT

    try:
        prio_enum = NotificationPriority(priority.lower())
    except ValueError:
        prio_enum = NotificationPriority.MEDIUM

    notif = Notification(
        id=uuid4(),
        institution_id=institution_id,
        recipient_id=recipient_id,
        category=cat_enum,
        title=title.strip(),
        body=body.strip(),
        priority=prio_enum,
        action_url=action_url,
        source_id=source_id,
        is_read=False,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # Check recipient preferences for email delivery
    pref_stmt = select(NotificationPreference).where(
        and_(
            NotificationPreference.user_id == recipient_id,
            NotificationPreference.category == cat_enum,
            NotificationPreference.institution_id == institution_id,
        )
    )
    pref = (await db.execute(pref_stmt)).scalar_one_or_none()
    should_email = pref.email_enabled if pref else (prio_enum in (NotificationPriority.HIGH, NotificationPriority.URGENT))

    if should_email:
        user_stmt = select(User.email).where(User.id == recipient_id)
        recipient_email = (await db.execute(user_stmt)).scalar_one_or_none()
        if recipient_email:
            await _dispatch_email(recipient_email, title, body)

    return _model_to_dict(notif)


async def bulk_notify_students(
    db: AsyncSession,
    institution_id: UUID,
    student_ids: list[UUID],
    category: str,
    title: str,
    body: str,
    priority: str = "medium",
) -> list[dict]:
    """Bulk creates in-app notifications for a list of students."""
    try:
        cat_enum = NotificationCategory(category.lower())
    except ValueError:
        cat_enum = NotificationCategory.ACADEMIC_ANNOUNCEMENT

    try:
        prio_enum = NotificationPriority(priority.lower())
    except ValueError:
        prio_enum = NotificationPriority.MEDIUM

    notifs = []
    for s_id in student_ids:
        n = Notification(
            id=uuid4(),
            institution_id=institution_id,
            recipient_id=s_id,
            category=cat_enum,
            title=title.strip(),
            body=body.strip(),
            priority=prio_enum,
            is_read=False,
        )
        db.add(n)
        notifs.append(n)

    await db.commit()
    for n in notifs:
        await db.refresh(n)

    return [_model_to_dict(n) for n in notifs]


async def get_notifications(
    db: AsyncSession,
    institution_id: UUID,
    user_id: UUID,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Retrieves paginated notifications for a user."""
    conditions = [
        Notification.recipient_id == user_id,
        Notification.institution_id == institution_id,
    ]
    if unread_only:
        conditions.append(Notification.is_read.is_(False))

    stmt = (
        select(Notification)
        .where(and_(*conditions))
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    notifs = result.scalars().all()
    return [_model_to_dict(n) for n in notifs]


async def mark_notification_read(
    db: AsyncSession,
    institution_id: UUID,
    notification_id: UUID,
    user_id: UUID,
) -> dict:
    """Marks a single notification as read."""
    stmt = select(Notification).where(
        and_(
            Notification.id == notification_id,
            Notification.recipient_id == user_id,
            Notification.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    notif = result.scalar_one_or_none()
    if notif is None:
        raise ValueError(f"Notification {notification_id} not found.")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return _model_to_dict(notif)


async def mark_all_read(
    db: AsyncSession,
    institution_id: UUID,
    user_id: UUID,
) -> int:
    """Marks all unread notifications for a user as read."""
    now = datetime.now(timezone.utc)
    stmt = (
        update(Notification)
        .where(
            and_(
                Notification.recipient_id == user_id,
                Notification.institution_id == institution_id,
                Notification.is_read.is_(False),
            )
        )
        .values(is_read=True, read_at=now)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0


async def get_unread_count(
    db: AsyncSession,
    institution_id: UUID,
    user_id: UUID,
) -> int:
    """Counts unread notifications for a user."""
    stmt = select(func.count(Notification.id)).where(
        and_(
            Notification.recipient_id == user_id,
            Notification.institution_id == institution_id,
            Notification.is_read.is_(False),
        )
    )
    count = (await db.execute(stmt)).scalar() or 0
    return count


async def send_deadline_reminders_for_institution(
    db: AsyncSession,
    institution_id: UUID,
) -> int:
    """
    Find upcoming deadlines within each student's preferred advance_days
    window and create reminder notifications if not already sent.
    Returns count of notifications created.
    """
    now = datetime.now(timezone.utc)
    max_horizon = now + timedelta(days=7)

    # Find pending academic tasks due in next 7 days
    task_stmt = select(AcademicTask).where(
        and_(
            AcademicTask.institution_id == institution_id,
            AcademicTask.status.in_([AcademicTaskStatus.PENDING, AcademicTaskStatus.ACTIVE]),
            AcademicTask.due_date >= now,
            AcademicTask.due_date <= max_horizon,
        )
    )
    tasks = (await db.execute(task_stmt)).scalars().all()

    created_count = 0
    for task in tasks:
        # Check student advance_days preference
        pref_stmt = select(NotificationPreference.advance_days).where(
            and_(
                NotificationPreference.user_id == task.student_id,
                NotificationPreference.category == NotificationCategory.UPCOMING_DEADLINE,
                NotificationPreference.institution_id == institution_id,
            )
        )
        advance_days = (await db.execute(pref_stmt)).scalar() or 3

        threshold_dt = now + timedelta(days=advance_days)
        if task.due_date <= threshold_dt:
            # Check if reminder already sent in last 24 hours
            recent_since = now - timedelta(hours=24)
            check_notif = select(Notification.id).where(
                and_(
                    Notification.recipient_id == task.student_id,
                    Notification.category == NotificationCategory.UPCOMING_DEADLINE,
                    Notification.source_id == task.id,
                    Notification.created_at >= recent_since,
                )
            )
            already_sent = (await db.execute(check_notif)).scalar_one_or_none()
            if not already_sent:
                rem_notif = Notification(
                    id=uuid4(),
                    institution_id=institution_id,
                    recipient_id=task.student_id,
                    category=NotificationCategory.UPCOMING_DEADLINE,
                    title=f"Upcoming Deadline: {task.title}",
                    body=f"Your task '{task.title}' is due in {(task.due_date - now).days} day(s) on {task.due_date.strftime('%Y-%m-%d %H:%M')}.",
                    priority=NotificationPriority.HIGH,
                    source_id=task.id,
                )
                db.add(rem_notif)
                created_count += 1

    if created_count > 0:
        await db.commit()

    return created_count

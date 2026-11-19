"""
Celery Notification Tasks
"""
import asyncio
import logging
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    name='app.worker.tasks.notifications.send_deadline_reminders',
    bind=True,
)
def send_deadline_reminders(self):
    """Send deadline reminder notifications to students."""
    logger.info('Sending deadline reminders')
    try:
        run_async(_send_reminders())
    except Exception as exc:
        logger.error('Deadline reminders task failed: %s', exc)


async def _send_reminders():
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.institution import Institution
    from app.models.academic_task import AcademicTask
    from app.models.notification import Notification

    async with AsyncSessionLocal() as db:
        inst_result = await db.execute(
            select(Institution).where(Institution.is_active == True)
        )
        institutions = inst_result.scalars().all()

        now = datetime.utcnow()
        for institution in institutions:
            # Find tasks due in next 1, 3, 7 days that haven't been notified
            for days_ahead in [1, 3, 7]:
                target_date = now + timedelta(days=days_ahead)
                window_start = target_date.replace(hour=0, minute=0, second=0)
                window_end = target_date.replace(hour=23, minute=59, second=59)

                task_result = await db.execute(
                    select(AcademicTask).where(
                        AcademicTask.institution_id == institution.id,
                        AcademicTask.status.in_(['pending', 'active']),
                        AcademicTask.due_date >= window_start,
                        AcademicTask.due_date <= window_end,
                    )
                )
                tasks = task_result.scalars().all()

                for task in tasks:
                    notif = Notification(
                        institution_id=institution.id,
                        recipient_id=task.student_id,
                        category='upcoming_deadline',
                        title=f'Deadline in {days_ahead} day(s): {task.title}',
                        body=f'Your task "{task.title}" is due in {days_ahead} day(s).',
                        priority='high' if days_ahead == 1 else 'medium',
                        source_id=task.id,
                    )
                    db.add(notif)

        await db.commit()
        logger.info('Deadline reminders sent')

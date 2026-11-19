"""Queue maintenance tasks."""
import asyncio
import logging
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name='app.worker.tasks.queue_maintenance.mark_overdue_tasks')
def mark_overdue_tasks():
    """Mark pending tasks past their due date as overdue."""
    logger.info('Running overdue task scan')
    run_async(_mark_overdue())


async def _mark_overdue():
    from datetime import datetime
    from sqlalchemy import update
    from app.core.database import AsyncSessionLocal
    from app.models.academic_task import AcademicTask

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            update(AcademicTask)
            .where(
                AcademicTask.status == 'pending',
                AcademicTask.due_date < datetime.utcnow(),
            )
            .values(status='overdue')
            .returning(AcademicTask.id)
        )
        updated = result.fetchall()
        await db.commit()
        logger.info('Marked %d tasks as overdue', len(updated))

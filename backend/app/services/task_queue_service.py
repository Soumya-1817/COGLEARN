"""
Academic Task Queue Service
===========================
Manages each student's personal academic workload queue.

Queue design:
- Strict FIFO ordering by arrival_timestamp and assigned queue_position
- queue_position is set at creation and NEVER changed (immutable)
- due_date is a separate urgency attribute, NOT queue position
- Completed tasks leave the pending queue but remain in academic history

Task lifecycle:
  pending -> active (student begins working)
          -> completed (submission recorded)
          -> overdue (past due_date, still pending)
          -> cancelled (teacher cancels assignment)

Every status change is recorded in task_status_history.
"""

from datetime import date, datetime, timezone
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, asc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_task import AcademicTask, AcademicTaskStatus, AcademicTaskType
from app.models.deadline_extension import DeadlineExtension
from app.models.enrolment import CourseEnrolment, EnrolmentStatus
from app.models.task_status_history import TaskStatusHistory

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


def _dispatch_async_workload_recalculation(student_ids: list[UUID] | None = None) -> None:
    """Dispatches background Celery task for Model 3 workload recalculation."""
    try:
        from app.worker.tasks.analytics import run_nightly_workload_calculation
        run_nightly_workload_calculation.delay()
    except Exception as exc:
        logger.warning("Could not dispatch async Celery workload task: %s", exc)


async def create_task_for_student(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    course_id: UUID,
    task_type: str,
    source_id: UUID,
    title: str,
    description: str,
    due_date: datetime,
    estimated_workload: float,
    workload_weight: float,
    module_id: Optional[UUID] = None,
) -> dict:
    """
    Create a new academic task for a student.
    Assigns strict FIFO queue position = current max + 1 for the student.
    Returns the created task record.
    """
    # 1. Determine next FIFO queue position
    pos_stmt = select(func.coalesce(func.max(AcademicTask.queue_position), 0)).where(
        and_(
            AcademicTask.student_id == student_id,
            AcademicTask.institution_id == institution_id,
        )
    )
    res = await db.execute(pos_stmt)
    next_pos = (res.scalar() or 0) + 1

    # Normalize task_type enum
    try:
        t_type = AcademicTaskType(task_type.lower())
    except ValueError:
        t_type = AcademicTaskType.ASSIGNMENT

    task = AcademicTask(
        id=uuid4(),
        institution_id=institution_id,
        student_id=student_id,
        course_id=course_id,
        module_id=module_id,
        task_type=t_type,
        source_id=source_id,
        title=title.strip(),
        description=description.strip() if description else None,
        arrival_timestamp=datetime.now(timezone.utc),
        queue_position=next_pos,
        due_date=due_date,
        estimated_workload=estimated_workload,
        workload_weight=workload_weight,  # PROVISIONAL
        status=AcademicTaskStatus.PENDING,
    )
    db.add(task)

    # Initial history log
    history = TaskStatusHistory(
        id=uuid4(),
        institution_id=institution_id,
        task_id=task.id,
        old_status=AcademicTaskStatus.PENDING,
        new_status=AcademicTaskStatus.PENDING,
        changed_by=student_id,
        reason="Initial queue insertion",
    )
    db.add(history)

    await db.commit()
    await db.refresh(task)
    return _model_to_dict(task)


async def bulk_create_tasks_for_course_students(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
    task_type: str,
    source_id: UUID,
    title: str,
    description: str,
    due_date: datetime,
    estimated_workload: float,
    workload_weight: float,
    module_id: Optional[UUID] = None,
) -> list[dict]:
    """
    Create tasks for all students enrolled in a course.
    Called when a teacher publishes an assignment/quiz/assessment.
    """
    stmt = select(CourseEnrolment.student_id).where(
        and_(
            CourseEnrolment.course_id == course_id,
            CourseEnrolment.institution_id == institution_id,
            CourseEnrolment.status == EnrolmentStatus.ENROLLED,
        )
    )
    student_ids = (await db.execute(stmt)).scalars().all()

    created_tasks = []
    for s_id in student_ids:
        task_dict = await create_task_for_student(
            db=db,
            institution_id=institution_id,
            student_id=s_id,
            course_id=course_id,
            task_type=task_type,
            source_id=source_id,
            title=title,
            description=description,
            due_date=due_date,
            estimated_workload=estimated_workload,
            workload_weight=workload_weight,  # PROVISIONAL
            module_id=module_id,
        )
        created_tasks.append(task_dict)

    return created_tasks


async def get_student_pending_queue(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
) -> list[dict]:
    """
    Return pending & active tasks in FIFO queue order (by queue_position ASC).
    Includes overdue flag based on current datetime vs due_date.
    """
    stmt = (
        select(AcademicTask)
        .where(
            and_(
                AcademicTask.student_id == student_id,
                AcademicTask.institution_id == institution_id,
                AcademicTask.status.in_(
                    [AcademicTaskStatus.PENDING, AcademicTaskStatus.ACTIVE, AcademicTaskStatus.OVERDUE]
                ),
            )
        )
        .order_by(asc(AcademicTask.queue_position))
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    now = datetime.now(timezone.utc)
    queue_items = []
    for task in tasks:
        d = _model_to_dict(task)
        # Defensive timezone normalization for SQLite test environments
        task_due = task.due_date if task.due_date.tzinfo else task.due_date.replace(tzinfo=timezone.utc)
        d["is_overdue"] = task_due < now and task.status != AcademicTaskStatus.COMPLETED
        queue_items.append(d)

    return queue_items


async def update_task_status(
    db: AsyncSession,
    institution_id: UUID,
    task_id: UUID,
    new_status: str,
    changed_by: UUID,
    reason: Optional[str] = None,
) -> dict:
    """
    Update task status and record in task_status_history.
    Returns updated task record.
    """
    stmt = select(AcademicTask).where(
        and_(
            AcademicTask.id == task_id,
            AcademicTask.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise ValueError(f"Task {task_id} not found.")

    old_status = task.status
    target_status = AcademicTaskStatus(new_status.lower())

    task.status = target_status
    if target_status == AcademicTaskStatus.COMPLETED and not task.completion_timestamp:
        task.completion_timestamp = datetime.now(timezone.utc)

    history = TaskStatusHistory(
        id=uuid4(),
        institution_id=institution_id,
        task_id=task.id,
        old_status=old_status,
        new_status=target_status,
        changed_by=changed_by,
        reason=reason,
    )
    db.add(history)

    await db.commit()
    await db.refresh(task)
    return _model_to_dict(task)


async def extend_task_deadline(
    db: AsyncSession,
    institution_id: UUID,
    task_id: UUID,
    new_due_date: datetime,
    mentor_id: UUID,
    reason: str,
) -> dict:
    """
    Extend a task's deadline.
    - Creates a deadline_extension record (original_due_date is preserved)
    - Updates academic_task.due_date
    - Updates calendar_event
    - Sends deadline_extension notification to student
    - Triggers Model 3 workload recalculation (Celery)
    Returns the deadline_extension record.
    """
    stmt = select(AcademicTask).where(
        and_(
            AcademicTask.id == task_id,
            AcademicTask.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise ValueError(f"Task {task_id} not found.")

    original_due_date = task.due_date

    extension = DeadlineExtension(
        id=uuid4(),
        institution_id=institution_id,
        task_id=task.id,
        assignment_id=task.source_id if task.task_type == AcademicTaskType.ASSIGNMENT else None,
        quiz_id=task.source_id if task.task_type == AcademicTaskType.QUIZ else None,
        student_id=task.student_id,
        original_due_date=original_due_date,
        new_due_date=new_due_date,
        granted_by_mentor_id=mentor_id,
        reason=reason,
    )
    db.add(extension)

    # Update task due date
    now = datetime.now(timezone.utc)
    new_due_norm = new_due_date if new_due_date.tzinfo else new_due_date.replace(tzinfo=timezone.utc)
    task.due_date = new_due_date
    if task.status == AcademicTaskStatus.OVERDUE and new_due_norm > now:
        task.status = AcademicTaskStatus.PENDING

    # Update calendar event
    from app.services.calendar_service import update_calendar_event_deadline
    await update_calendar_event_deadline(
        db=db,
        institution_id=institution_id,
        student_id=task.student_id,
        source_task_id=task.id,
        new_due_date=new_due_date,
    )

    # Send notification to student
    from app.services.notification_service import create_notification
    from app.models.notification import NotificationCategory, NotificationPriority
    await create_notification(
        db=db,
        institution_id=institution_id,
        recipient_id=task.student_id,
        category=NotificationCategory.DEADLINE_EXTENSION.value,
        title=f"Deadline Extended: {task.title}",
        body=f"Your deadline for '{task.title}' has been extended to {new_due_date.strftime('%Y-%m-%d %H:%M')}. Reason: {reason}",
        priority=NotificationPriority.HIGH.value,
        source_id=task.id,
    )

    await db.commit()
    await db.refresh(extension)

    _dispatch_async_workload_recalculation([task.student_id])
    return _model_to_dict(extension)


async def mark_overdue_tasks(
    db: AsyncSession,
    institution_id: UUID,
) -> int:
    """
    Scan all pending and active tasks past their due_date and mark them overdue.
    Called by Celery beat task. Returns count of tasks updated.
    """
    now = datetime.now(timezone.utc)
    stmt = select(AcademicTask).where(
        and_(
            AcademicTask.institution_id == institution_id,
            AcademicTask.status.in_([AcademicTaskStatus.PENDING, AcademicTaskStatus.ACTIVE]),
            AcademicTask.due_date < now,
        )
    )
    result = await db.execute(stmt)
    overdue_tasks = result.scalars().all()

    count = 0
    for task in overdue_tasks:
        old_status = task.status
        task.status = AcademicTaskStatus.OVERDUE
        history = TaskStatusHistory(
            id=uuid4(),
            institution_id=institution_id,
            task_id=task.id,
            old_status=old_status,
            new_status=AcademicTaskStatus.OVERDUE,
            changed_by=task.student_id,
            reason="Automated deadline cutoff detection",
        )
        db.add(history)
        count += 1

    if count > 0:
        await db.commit()

    return count


async def calculate_student_weighted_workload(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
) -> dict:
    """
    Calculate current workload breakdown using task weights.
    Returns: {incoming, active, completed, overdue, total_weighted}
    This feeds into Model 3 workload calculation.
    """
    stmt = select(AcademicTask).where(
        and_(
            AcademicTask.student_id == student_id,
            AcademicTask.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    incoming_load = 0.0
    active_load = 0.0
    completed_load = 0.0
    overdue_load = 0.0

    for t in tasks:
        # Load contribution = estimated_workload * workload_weight
        w_val = float(t.estimated_workload) * float(t.workload_weight)
        if t.status == AcademicTaskStatus.PENDING:
            incoming_load += w_val
        elif t.status == AcademicTaskStatus.ACTIVE:
            active_load += w_val
        elif t.status == AcademicTaskStatus.COMPLETED:
            completed_load += w_val
        elif t.status == AcademicTaskStatus.OVERDUE:
            overdue_load += w_val

    total_weighted = incoming_load + active_load + overdue_load

    return {
        "incoming": round(incoming_load, 2),
        "active": round(active_load, 2),
        "completed": round(completed_load, 2),
        "overdue": round(overdue_load, 2),
        "total_weighted": round(total_weighted, 2),
    }

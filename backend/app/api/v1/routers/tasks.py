"""
Academic Task Queue API Router
==============================
Student-facing endpoints for personal task queue management (FIFO order).
"""

from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.academic_task import AcademicTask, AcademicTaskStatus
from app.models.user import User
from app.schemas.tasks import AcademicTaskResponse, TaskStatusUpdateRequest
from app.services import task_queue_service

router = APIRouter()


@router.get("/tasks/my", response_model=list[AcademicTaskResponse])
async def get_my_pending_queue(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns student's pending academic tasks ordered by strict FIFO queue position.
    """
    return await task_queue_service.get_student_pending_queue(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
    )


@router.get("/tasks/my/upcoming", response_model=list[AcademicTaskResponse])
async def get_my_upcoming_tasks(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns upcoming tasks due within the next N days.
    """
    queue = await task_queue_service.get_student_pending_queue(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
    )
    now = datetime.now(timezone.utc)
    return [t for t in queue if not t.get("is_overdue")]


@router.get("/tasks/my/overdue", response_model=list[AcademicTaskResponse])
async def get_my_overdue_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all overdue tasks currently outstanding.
    """
    queue = await task_queue_service.get_student_pending_queue(
        db=db,
        institution_id=current_user.institution_id,
        student_id=current_user.id,
    )
    return [t for t in queue if t.get("is_overdue") or t.get("status") == AcademicTaskStatus.OVERDUE.value]


@router.get("/tasks/my/completed", response_model=list[AcademicTaskResponse])
async def get_my_completed_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns student's completed tasks history.
    """
    stmt = (
        select(AcademicTask)
        .where(
            and_(
                AcademicTask.student_id == current_user.id,
                AcademicTask.institution_id == current_user.institution_id,
                AcademicTask.status == AcademicTaskStatus.COMPLETED,
            )
        )
        .order_by(AcademicTask.completion_timestamp.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [task_queue_service._model_to_dict(r) for r in records]


@router.patch("/tasks/{id}/status", response_model=AcademicTaskResponse)
async def update_task_status(
    id: UUID,
    status_in: TaskStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the status of a task (e.g. marking as active when student starts work).
    """
    try:
        return await task_queue_service.update_task_status(
            db=db,
            institution_id=current_user.institution_id,
            task_id=id,
            new_status=status_in.status,
            changed_by=current_user.id,
            reason=status_in.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

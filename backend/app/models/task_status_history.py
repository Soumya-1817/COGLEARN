from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.academic_task import AcademicTaskStatus


class TaskStatusHistory(Base):
    """
    Audit log of state transitions for academic tasks in the student queue.
    """
    __tablename__ = "task_status_histories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("academic_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    old_status: Mapped[AcademicTaskStatus] = mapped_column(
        Enum(AcademicTaskStatus, name="academic_task_status_enum", native_enum=False),
        nullable=False,
    )
    new_status: Mapped[AcademicTaskStatus] = mapped_column(
        Enum(AcademicTaskStatus, name="academic_task_status_enum", native_enum=False),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    changed_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    task: Mapped["AcademicTask"] = relationship("AcademicTask", lazy="selectin")
    user: Mapped["User"] = relationship("User", lazy="selectin")

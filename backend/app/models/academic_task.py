from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AcademicTaskType(str, enum.Enum):
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    ASSESSMENT = "assessment"


class AcademicTaskStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class AcademicTask(Base):
    """
    Academic Task queue item for a student.
    Tracks arrival order (FIFO queue position) for M/M/1 queue processing.
    """
    __tablename__ = "academic_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("modules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_type: Mapped[AcademicTaskType] = mapped_column(
        Enum(AcademicTaskType, name="academic_task_type_enum", native_enum=False),
        nullable=False,
    )
    source_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    arrival_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    # Strict FIFO queue position; assigned upon task entry to queue and immutable
    queue_position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    estimated_workload: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    # ICAP workload weight for task; PROVISIONAL until empirical validation
    workload_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # PROVISIONAL
    status: Mapped[AcademicTaskStatus] = mapped_column(
        Enum(AcademicTaskStatus, name="academic_task_status_enum", native_enum=False),
        default=AcademicTaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    completion_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submission_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    course: Mapped["Course"] = relationship("Course", lazy="selectin")
    module: Mapped["Module | None"] = relationship("Module", lazy="selectin")

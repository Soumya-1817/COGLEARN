from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeadlineExtension(Base):
    """
    Mentor-granted deadline extension record.
    Preserves original_due_date immutably for risk audit and queue re-scheduling.
    """
    __tablename__ = "deadline_extensions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("academic_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    quiz_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Immutable baseline: never overwritten or modified
    original_due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    new_due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    granted_by_mentor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    task: Mapped["AcademicTask"] = relationship("AcademicTask", lazy="selectin")
    student: Mapped["User"] = relationship(
        "User", foreign_keys=[student_id], lazy="selectin"
    )
    mentor: Mapped["User"] = relationship(
        "User", foreign_keys=[granted_by_mentor_id], lazy="selectin"
    )

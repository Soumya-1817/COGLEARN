from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssessmentType(str, enum.Enum):
    MIDTERM = "midterm"
    FINAL = "final"
    PROJECT = "project"
    PRESENTATION = "presentation"


class Assessment(Base):
    """
    High-stakes Academic Assessment entity (midterm, final, project presentation).
    """
    __tablename__ = "assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment_type: Mapped[AssessmentType] = mapped_column(
        Enum(AssessmentType, name="assessment_type_enum", native_enum=False),
        nullable=False,
    )
    scheduled_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # ICAP workload weight for high-stakes assessment; PROVISIONAL until empirical validation
    workload_weight: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)  # PROVISIONAL
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    course: Mapped["Course"] = relationship("Course", lazy="selectin")
    teacher: Mapped["User"] = relationship("User", lazy="selectin")

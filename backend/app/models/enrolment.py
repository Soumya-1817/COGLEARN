from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnrolmentStatus(str, enum.Enum):
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"


class CourseEnrolment(Base):
    """
    Student Course Enrolment record.
    """
    __tablename__ = "course_enrolments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_enrolment"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[EnrolmentStatus] = mapped_column(
        Enum(EnrolmentStatus, name="enrolment_status_enum", native_enum=False),
        default=EnrolmentStatus.ENROLLED,
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    course: Mapped["Course"] = relationship("Course", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")

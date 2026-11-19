from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ActivityEventType(str, enum.Enum):
    NAVIGATE = "navigate"
    OPEN_RESOURCE = "open_resource"
    WATCH_VIDEO = "watch_video"
    READ_PDF = "read_pdf"
    TAKE_NOTES = "take_notes"
    ATTEMPT_QUIZ = "attempt_quiz"
    COMPLETE_ASSIGNMENT = "complete_assignment"
    PREPARE_PROJECT = "prepare_project"
    SUBMIT_ASSESSMENT = "submit_assessment"
    LOGIN = "login"
    LOGOUT = "logout"
    DOWNLOAD = "download"


class ActivityEvent(Base):
    """
    Fine-grained student telemetry activity event representing an interaction in the LMS.
    """
    __tablename__ = "activity_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lesson_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[ActivityEventType] = mapped_column(
        Enum(ActivityEventType, name="activity_event_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    event_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        server_default="{}",
        default=dict,
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    session_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    is_anomalous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    anomaly_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    course: Mapped["Course | None"] = relationship("Course", lazy="selectin")
    lesson: Mapped["Lesson | None"] = relationship("Lesson", lazy="selectin")

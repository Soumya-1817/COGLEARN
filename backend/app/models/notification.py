from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationCategory(str, enum.Enum):
    ACADEMIC_ANNOUNCEMENT = "academic_announcement"
    NEW_ASSIGNMENT = "new_assignment"
    UPCOMING_DEADLINE = "upcoming_deadline"
    ASSESSMENT_REMINDER = "assessment_reminder"
    MENTOR_MESSAGE = "mentor_message"
    DEADLINE_EXTENSION = "deadline_extension"
    UNIVERSITY_ANNOUNCEMENT = "university_announcement"
    SUPPORT_NOTIFICATION = "support_notification"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """
    User notifications dispatched through in-app and email channels.
    """
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, name="notification_category_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, name="notification_priority_enum", native_enum=False),
        default=NotificationPriority.MEDIUM,
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    recipient: Mapped["User"] = relationship("User", lazy="selectin")

from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterventionTriggerType(str, enum.Enum):
    IORI_THRESHOLD = "iori_threshold"
    MANUAL = "manual"
    STUDENT_REQUEST = "student_request"


class InterventionStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class Intervention(Base):
    """
    Mentorship intervention workflow triggered by high cognitive risk (IORI) or manual referral.
    """
    __tablename__ = "interventions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mentor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_type: Mapped[InterventionTriggerType] = mapped_column(
        Enum(InterventionTriggerType, name="intervention_trigger_type_enum", native_enum=False),
        nullable=False,
    )
    iori_value_at_trigger: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_zone_at_trigger: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, name="intervention_status_enum", native_enum=False),
        default=InterventionStatus.OPEN,
        nullable=False,
        index=True,
    )
    summary_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    mentor: Mapped["User"] = relationship("User", foreign_keys=[mentor_id], lazy="selectin")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], lazy="selectin")

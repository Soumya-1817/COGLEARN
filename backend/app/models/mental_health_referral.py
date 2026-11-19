from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"


class MentalHealthReferral(Base):
    """
    RESTRICTED: Mental Health and Counseling Referral Entity.
    Requires explicit authorization claim 'referral:read'.
    In production deployments, referral_body is encrypted at rest using envelope encryption.
    """
    __tablename__ = "mental_health_referrals"
    __table_args__ = {
        "comment": "RESTRICTED — requires explicit authorization claim referral:read",
    }

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referred_by_mentor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    referral_body: Mapped[str] = mapped_column(Text, nullable=False)
    consent_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, name="referral_status_enum", native_enum=False),
        default=ReferralStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship(
        "User", foreign_keys=[student_id], lazy="selectin"
    )
    mentor: Mapped["User"] = relationship(
        "User", foreign_keys=[referred_by_mentor_id], lazy="selectin"
    )

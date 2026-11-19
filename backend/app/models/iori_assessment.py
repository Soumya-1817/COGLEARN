from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskZone(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class IORIAssessment(Base):
    """
    Index of Overload and Risk of Ineffectiveness (IORI) Assessment.

    Mathematical Formulation:
    -------------------------
    Definition:
        IORI(t) = P(S_t = Overload | O_1:t) + P(S_t = Fatigue | O_1:t)
        where P(S_t | O_1:t) is derived from Model 4 HMM forward posterior.

    Classification Zones (PROVISIONAL thresholds):
        - Green  (Stable / Safe):     0.00 <= IORI < 0.35   # PROVISIONAL
        - Yellow (Attentive Caution): 0.35 <= IORI < 0.65   # PROVISIONAL
        - Red    (Acute Risk):        0.65 <= IORI <= 1.00  # PROVISIONAL

    Access Governance:
        Strictly RESTRICTED to Academic Mentors and Administrative Staff.
        Student-facing endpoints must never leak IORI, state posteriors, or raw risk zones.
    """
    __tablename__ = "iori_assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    iori_value: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    risk_zone: Mapped[RiskZone] = mapped_column(
        Enum(RiskZone, name="risk_zone_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    p_overload: Mapped[float] = mapped_column(Float, nullable=False)
    p_fatigue: Mapped[float] = mapped_column(Float, nullable=False)
    hmm_estimate_id: Mapped[UUID] = mapped_column(
        ForeignKey("hmm_state_estimates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    queue_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("queue_metric_snapshots.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_presented_to_mentor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mentor_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    hmm_estimate: Mapped["HMMStateEstimate"] = relationship("HMMStateEstimate", lazy="selectin")
    queue_snapshot: Mapped["QueueMetricSnapshot | None"] = relationship(
        "QueueMetricSnapshot", lazy="selectin"
    )
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", lazy="selectin")


# Alias for flexible imports
IoriAssessment = IORIAssessment

from datetime import date, datetime
from uuid import UUID, uuid4
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IncomingWorkloadObservation(Base):
    """
    Model 3 Output: Incoming Workload Observation (lambda).

    Mathematical Formulation:
    -------------------------
    1. Raw Workload Demand:
       lambda_{raw}(t) = sum_{k in Events} w_k * C_k(t)
       where:
         - C_k(t) is the count of event type k on day t.
         - w_k is the ICAP-informed weight from ActivityWeightConfig:
           * Passive: w_passive = 0.5   # PROVISIONAL
           * Active: w_active = 1.0     # PROVISIONAL
           * Constructive: w_constructive = 1.8 # PROVISIONAL
           * Interactive: w_interactive = 2.5   # PROVISIONAL

    2. Causal 3-Day Moving Average:
       lambda_{smoothed}(t) = (lambda_{raw}(t) + lambda_{raw}(t-1) + lambda_{raw}(t-2)) / 3.0
       Note: Causal filtering prevents lookahead bias in queueing stability prediction.

    3. Workload Partitioning:
       W_{total}(t) = W_{incoming}(t) + W_{active}(t) + W_{overdue}(t)
    """
    __tablename__ = "incoming_workload_observations"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_student_workload_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    raw_lambda: Mapped[float] = mapped_column(Float, nullable=False)
    smoothed_lambda: Mapped[float] = mapped_column(Float, nullable=False)
    incoming_workload: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    active_workload: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completed_workload: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overdue_workload: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ineffective_interactions: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    weight_config_version: Mapped[str] = mapped_column(
        String(50), default="v1.0-provisional", nullable=False
    )
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", lazy="selectin")

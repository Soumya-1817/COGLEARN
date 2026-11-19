from datetime import date, datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QueueMetricSnapshot(Base):
    """
    Model 2 Output: M/M/1 Cognitive Queueing Metrics.

    Mathematical Formulation:
    -------------------------
    Assumptions:
        - Arrival process of cognitive tasks: Poisson with rate lambda (demand).
        - Service time (cognitive processing): Exponential with rate mu (capacity).
        - Single cognitive processor (M/M/1 queue).

    Formulas:
        1. Utilization Ratio (Traffic Intensity):
           rho = lambda / mu

        2. Stability Criterion:
           is_stable = (rho < 1.0) and (lambda < mu)

        3. Expected Tasks in System (Queue Length):
           L = rho / (1.0 - rho) = lambda / (mu - lambda)  [defined iff rho < 1.0]

        4. Expected Total Time in System (Little's Law):
           W = L / lambda = 1.0 / (mu - lambda)             [defined iff rho < 1.0]

        5. Instability Behavior:
           If rho >= 1.0, the queue is unstable (divergent cognitive backlog).
           L and W become mathematically undefined (+infinity), stored as NULL with
           is_stable=False and instability_reason='Cognitive demand lambda exceeds processing capacity mu'.
    """
    __tablename__ = "queue_metric_snapshots"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_student_queue_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    lambda_demand: Mapped[float] = mapped_column(Float, nullable=False)
    mu_capacity: Mapped[float] = mapped_column(Float, nullable=False)
    rho: Mapped[float] = mapped_column(Float, nullable=False)
    L: Mapped[float | None] = mapped_column(Float, nullable=True)
    W: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_stable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    instability_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", lazy="selectin")

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CalculationAuditLog(Base):
    """
    Audit log of mathematical model executions.
    Guarantees reproducibility and algorithmic accountability.
    """
    __tablename__ = "calculation_audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    input_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        server_default="{}",
        default=dict,
        nullable=False,
    )
    output_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        server_default="{}",
        default=dict,
        nullable=False,
    )
    calculation_duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    triggered_by: Mapped[str] = mapped_column(
        String(50), default="scheduled", nullable=False
    )  # 'scheduled', 'event', 'manual'

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", lazy="selectin")

from datetime import date, datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ICAPLevel(str, enum.Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
    CONSTRUCTIVE = "constructive"
    INTERACTIVE = "interactive"


class ActivityWeightConfig(Base):
    """
    Configuration table assigning ICAP framework weights to telemetry activity events.
    Weights are marked PROVISIONAL until validated against longitudinal cognitive performance data.
    """
    __tablename__ = "activity_weight_configs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    icap_level: Mapped[ICAPLevel] = mapped_column(
        Enum(ICAPLevel, name="icap_level_enum", native_enum=False),
        nullable=False,
    )
    # ICAP workload weight; PROVISIONAL until research validates
    weight: Mapped[float] = mapped_column(Float, nullable=False)  # PROVISIONAL
    version: Mapped[str] = mapped_column(String(50), default="v1.0-provisional", nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    deprecated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(
        Text,
        default="PROVISIONAL: ICAP framework weights subject to empirical validation.",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")

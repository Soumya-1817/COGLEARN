from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelVersion(Base):
    """
    Registry for mathematical model parameter sets (Models 1, 2, 3, and 4).
    Enables reproducible analytics audit trails and versioned parameter updates.
    """
    __tablename__ = "model_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    model_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    version_string: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    parameters: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        server_default="{}",
        default=dict,
        nullable=False,
    )
    is_provisional: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # PROVISIONAL
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

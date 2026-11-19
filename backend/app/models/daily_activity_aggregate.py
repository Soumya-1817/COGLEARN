from datetime import date, datetime
from uuid import UUID, uuid4
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DailyActivityAggregate(Base):
    """
    Daily aggregated telemetry and ICAP-weighted interaction metrics per student.
    Forms the empirical input to Model 1 (Capacity) and Model 3 (Workload).
    """
    __tablename__ = "daily_activity_aggregates"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_student_daily_activity"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weighted_clicks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    valid_click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    anomalous_click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    session_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_courses_accessed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")

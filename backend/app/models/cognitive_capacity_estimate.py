from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CognitiveCapacityEstimate(Base):
    """
    Model 1 Output: Bayesian Estimation of Cognitive Processing Capacity (mu).

    Mathematical Formulation:
    -------------------------
    Prior Distribution:
        mu ~ Gamma(alpha_0, beta_0)
        where alpha_0 is the prior shape parameter and beta_0 is the prior rate parameter.
        (PROVISIONAL priors: alpha_0 = 10.0, beta_0 = 2.0 based on initial cohort telemetry).

    Likelihood Model:
        Given daily observed effective workload processed y_1, y_2, ..., y_n ~ Poisson(mu):
        L(mu | y) = prod_{i=1}^n (mu^{y_i} * e^{-mu} / y_i!)

    Posterior Conjugate Update:
        mu | y_1:n ~ Gamma(alpha_post, beta_post)
        alpha_post = alpha_0 + sum_{i=1}^n y_i
        beta_post  = beta_0 + n

    Point and Interval Estimates:
        E[mu] = alpha_post / beta_post
        Var(mu) = alpha_post / (beta_post^2)
        95% Credible Interval: [F^{-1}(0.025; alpha_post, beta_post), F^{-1}(0.975; alpha_post, beta_post)]
    """
    __tablename__ = "cognitive_capacity_estimates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alpha_post: Mapped[float] = mapped_column(Float, nullable=False)
    beta_post: Mapped[float] = mapped_column(Float, nullable=False)
    mean_capacity: Mapped[float] = mapped_column(Float, nullable=False)
    variance: Mapped[float] = mapped_column(Float, nullable=False)
    ci_lower_95: Mapped[float] = mapped_column(Float, nullable=False)
    ci_upper_95: Mapped[float] = mapped_column(Float, nullable=False)
    n_observations: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_provisional_params: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # PROVISIONAL
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", lazy="selectin")

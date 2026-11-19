from datetime import datetime
import enum
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CognitiveState(str, enum.Enum):
    UNDERLOAD = "underload"
    FLOW = "flow"
    OVERLOAD = "overload"
    FATIGUE = "fatigue"


class HMMStateEstimate(Base):
    """
    Model 4 Output: Hidden Markov Model (HMM) Latent Cognitive State Probabilities.

    Mathematical Formulation:
    -------------------------
    Hidden States:
        S in { Underload (1), Flow (2), Overload (3), Fatigue (4) }

    Observation Vector at step t:
        O_t = [ rho_t, ineffective_interaction_ratio_t, overdue_task_count_t, session_duration_t ]

    Model Parameters:
        - Initial State Distribution: pi = [ P(S_1 = s) ]
        - Transition Matrix: A_{ij} = P(S_t = j | S_{t-1} = i)  # PROVISIONAL
        - Emission Distribution: B_j(O_t) = P(O_t | S_t = j)   # PROVISIONAL Gaussian mixture / multivariate normal

    Forward Filter Algorithm:
        1. Initialization:
           alpha_1(j) = pi_j * B_j(O_1)
        2. Induction (Recursive Forward Step):
           alpha_t(j) = B_j(O_t) * sum_{i=1}^4 ( alpha_{t-1}(i) * A_{ij} )
        3. Normalized Posterior State Probabilities:
           P(S_t = j | O_1:t) = alpha_t(j) / sum_{k=1}^4 alpha_t(k)

    Dominant State:
        s* = argmax_{s in S} P(S_t = s | O_1:t)
    """
    __tablename__ = "hmm_state_estimates"

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
    p_underload: Mapped[float] = mapped_column(Float, nullable=False)
    p_flow: Mapped[float] = mapped_column(Float, nullable=False)
    p_overload: Mapped[float] = mapped_column(Float, nullable=False)
    p_fatigue: Mapped[float] = mapped_column(Float, nullable=False)
    dominant_state: Mapped[CognitiveState] = mapped_column(
        Enum(CognitiveState, name="cognitive_state_enum", native_enum=False),
        nullable=False,
    )
    observation_vector: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        server_default="{}",
        default=dict,
        nullable=False,
    )
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_provisional_params: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # PROVISIONAL

    institution: Mapped["Institution"] = relationship("Institution", lazy="selectin")
    student: Mapped["User"] = relationship("User", lazy="selectin")
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", lazy="selectin")


# Alias for flexible imports
HmmStateEstimate = HMMStateEstimate

"""
Model 4: Four-State Hidden Markov Model for Cognitive State Estimation
======================================================================
Estimates a student's latent cognitive state using a 4-state HMM with
real-time Forward Filtering (causal — uses only past and current observations).

States
------
  S0 = Underload  : Low arousal, boredom, disengagement
  S1 = Flow       : Optimal challenge-skill balance, productive engagement
  S2 = Overload   : Working-memory saturation, cognitive thrashing
  S3 = Fatigue    : Depleted stamina, slowed processing, withdrawal

HMM parameters: lambda_HMM = (pi, A, B)
  pi[i]    = P(q_1 = S_i)                       Initial state distribution
  A[i,j]   = P(q_t = S_j | q_{t-1} = S_i)      Transition matrix
  B[i,k]   = P(O_t = k | q_t = S_i)             Emission matrix

All parameters below are PROVISIONAL. They must be replaced with values
estimated from labelled student behavioural data via the Baum-Welch algorithm.

Forward filtering (normalized, underflow-safe)
-----------------------------------------------
Initialization (t=1):
  alpha_tilde_1(i) = pi_i * b_i(O_1)
  c_1              = 1 / sum_i alpha_tilde_1(i)
  alpha_hat_1(i)   = c_1 * alpha_tilde_1(i)

Recursion (t >= 2):
  alpha_tilde_t(j) = [sum_i alpha_hat_{t-1}(i) * A[i,j]] * b_j(O_t)
  c_t              = 1 / sum_j alpha_tilde_t(j)
  alpha_hat_t(j)   = c_t * alpha_tilde_t(j)

alpha_hat_t(j) = P(q_t = S_j | O_1,...,O_t)  — posterior filtered belief

Injection Complexity: O(K^2) = O(16) per step.

IORI (Intervention-Oriented Risk Index)
----------------------------------------
IORI(t) = P(Overload | O_{1:t}) + P(Fatigue | O_{1:t})
        = alpha_hat_t(S2) + alpha_hat_t(S3)
IORI in [0, 1].

IORI is a support indicator, NOT a medical diagnosis.
It must NEVER be shown directly to students via any API endpoint.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import numpy as np


# ---------------------------------------------------------------------------
# State definitions
# ---------------------------------------------------------------------------

class CognitiveState(str, Enum):
    UNDERLOAD = 'underload'
    FLOW      = 'flow'
    OVERLOAD  = 'overload'
    FATIGUE   = 'fatigue'

    @classmethod
    def from_index(cls, idx: int) -> 'CognitiveState':
        mapping = {0: cls.UNDERLOAD, 1: cls.FLOW, 2: cls.OVERLOAD, 3: cls.FATIGUE}
        return mapping[idx]


class RiskZone(str, Enum):
    GREEN  = 'green'   # IORI < 0.30
    YELLOW = 'yellow'  # 0.30 <= IORI < 0.60
    RED    = 'red'     # IORI >= 0.60


IORI_THRESHOLDS = {'green': 0.30, 'red': 0.60}


# ---------------------------------------------------------------------------
# PROVISIONAL HMM parameters
# Replace with Baum-Welch estimated values once labelled data is available.
# ---------------------------------------------------------------------------

# Initial state distribution (PROVISIONAL)
# Assumes most students start in Flow or Underload
PROVISIONAL_PI = np.array([
    0.10,  # S0 Underload  PROVISIONAL
    0.60,  # S1 Flow       PROVISIONAL
    0.20,  # S2 Overload   PROVISIONAL
    0.10,  # S3 Fatigue    PROVISIONAL
], dtype=np.float64)

# Transition probability matrix (PROVISIONAL)
# A[i,j] = P(S_j | S_i)
# States tend to persist; transitions between adjacent states more likely
PROVISIONAL_A = np.array([
    # To:  Underload  Flow   Overload  Fatigue
    [0.70,  0.25,     0.03,  0.02],   # From Underload  PROVISIONAL
    [0.10,  0.70,     0.15,  0.05],   # From Flow       PROVISIONAL
    [0.05,  0.20,     0.60,  0.15],   # From Overload   PROVISIONAL
    [0.05,  0.25,     0.20,  0.50],   # From Fatigue    PROVISIONAL
], dtype=np.float64)

# Observation discretisation
# rho (utilization ratio) is binned into 5 categories
RHO_BINS = [0.0, 0.3, 0.5, 0.8, 1.0, float('inf')]
# 0: very_low, 1: low, 2: medium, 3: high, 4: overload
N_OBS_SYMBOLS = 5

# Emission matrix B[state, obs_symbol] = P(obs | state)  PROVISIONAL
# Rows: states [Underload, Flow, Overload, Fatigue]
# Cols: observation bins [very_low, low, medium, high, overload]
PROVISIONAL_B = np.array([
    # very_low  low   medium  high  overload
    [0.60,     0.25,  0.10,   0.04,  0.01],  # Underload   PROVISIONAL
    [0.10,     0.30,  0.40,   0.15,  0.05],  # Flow        PROVISIONAL
    [0.02,     0.08,  0.25,   0.35,  0.30],  # Overload    PROVISIONAL
    [0.30,     0.30,  0.20,   0.15,  0.05],  # Fatigue     PROVISIONAL
], dtype=np.float64)


@dataclass
class HMMParameters:
    """Full HMM parameter set with provenance tracking."""
    pi: np.ndarray            # Shape (4,)
    A: np.ndarray             # Shape (4, 4)
    B: np.ndarray             # Shape (4, N_OBS_SYMBOLS)
    is_provisional: bool = True
    version: str = 'v1.0-provisional'
    n_states: int = 4
    state_labels: list[str] = field(default_factory=lambda: [
        'underload', 'flow', 'overload', 'fatigue'
    ])

    def validate(self):
        """Validate HMM parameter constraints."""
        assert self.pi.shape == (self.n_states,), 'pi shape mismatch'
        assert np.isclose(self.pi.sum(), 1.0, atol=1e-6), 'pi must sum to 1'
        assert self.A.shape == (self.n_states, self.n_states), 'A shape mismatch'
        assert np.allclose(self.A.sum(axis=1), 1.0, atol=1e-6), 'A rows must sum to 1'
        assert self.B.shape[0] == self.n_states, 'B state dimension mismatch'
        assert np.allclose(self.B.sum(axis=1), 1.0, atol=1e-6), 'B rows must sum to 1'

    @classmethod
    def provisional_default(cls) -> 'HMMParameters':
        params = cls(pi=PROVISIONAL_PI.copy(), A=PROVISIONAL_A.copy(), B=PROVISIONAL_B.copy())
        params.validate()
        return params


@dataclass
class ObservationVector:
    """
    Discretised observation at time t.
    rho_bin: int in [0, N_OBS_SYMBOLS)
    """
    rho: float            # Raw utilization ratio from Model 2
    rho_bin: int          # Discretised index
    raw_features: dict    # Full feature dict for audit


@dataclass
class HMMStateEstimate:
    """Forward-filtered posterior state distribution at time t."""
    student_id: str
    timestamp: datetime
    p_underload: float
    p_flow: float
    p_overload: float
    p_fatigue: float
    dominant_state: CognitiveState
    iori: float
    risk_zone: RiskZone
    observation_vector: dict  # Serialisable version for audit
    is_provisional_params: bool
    model_version: str

    @property
    def posterior(self) -> np.ndarray:
        return np.array([self.p_underload, self.p_flow, self.p_overload, self.p_fatigue])


def discretise_rho(rho: float) -> int:
    """
    Bin utilization ratio rho into N_OBS_SYMBOLS discrete observation indices.
    rho in [0, 0.3)   -> 0 (very_low)
    rho in [0.3, 0.5) -> 1 (low)
    rho in [0.5, 0.8) -> 2 (medium)
    rho in [0.8, 1.0) -> 3 (high)
    rho >= 1.0        -> 4 (overload)
    """
    rho = max(0.0, rho)
    for i in range(len(RHO_BINS) - 1):
        if rho < RHO_BINS[i + 1]:
            return i
    return len(RHO_BINS) - 2  # Last bin


def classify_risk_zone(iori: float) -> RiskZone:
    if iori < IORI_THRESHOLDS['green']:
        return RiskZone.GREEN
    elif iori < IORI_THRESHOLDS['red']:
        return RiskZone.YELLOW
    else:
        return RiskZone.RED


class RealTimeHMMFilter:
    """
    Real-time forward filter for the 4-state cognitive HMM.

    Maintains the current posterior belief alpha_hat over hidden states
    and updates it incrementally as new observations arrive.

    Uses normalized forward variables to prevent floating-point underflow:
      alpha_hat_t(j) = P(q_t = S_j | O_1,...,O_t)

    This filter is CAUSAL — it uses only past and current observations.
    It is suitable for real-time student monitoring.
    """

    def __init__(
        self,
        student_id: str,
        params: Optional[HMMParameters] = None,
    ):
        self.student_id = student_id
        self.params = params or HMMParameters.provisional_default()
        self.alpha_hat = self.params.pi.copy()  # Current belief
        self.log_likelihood: float = 0.0
        self.step_count: int = 0

    def _emission(self, obs_bin: int) -> np.ndarray:
        """Return emission probability vector b_j(O_t) for all states j."""
        return self.params.B[:, obs_bin].copy()

    def update(self, observation: ObservationVector) -> np.ndarray:
        """
        Perform one forward-filter update step.

        Algorithm:
          1. Predict: pred_j = sum_i alpha_hat_{t-1}(i) * A[i,j]
          2. Update:  alpha_tilde_t(j) = pred_j * b_j(O_t)
          3. Normalise: c_t = 1/sum(alpha_tilde); alpha_hat_t = c_t * alpha_tilde_t

        Parameters
        ----------
        observation : discretised observation at time t

        Returns
        -------
        alpha_hat : posterior P(q_t = S_j | O_{1:t}) for all j
        """
        # Step 1: State prediction
        pred = self.alpha_hat @ self.params.A  # Shape (4,)

        # Step 2: Measurement update (multiply by emission)
        b = self._emission(observation.rho_bin)
        alpha_tilde = pred * b

        # Step 3: Normalisation (prevents underflow)
        c_t = alpha_tilde.sum()
        if c_t < 1e-300 or not np.isfinite(c_t):
            # Degenerate observation — fall back to uniform belief
            self.alpha_hat = np.ones(self.params.n_states) / self.params.n_states
        else:
            self.alpha_hat = alpha_tilde / c_t
            self.log_likelihood += np.log(c_t)

        self.step_count += 1
        return self.alpha_hat.copy()

    def current_estimate(
        self,
        observation: ObservationVector,
        timestamp: Optional[datetime] = None,
    ) -> HMMStateEstimate:
        """
        Update with observation and return the full state estimate.
        """
        posterior = self.update(observation)
        p_underload, p_flow, p_overload, p_fatigue = posterior

        iori = float(p_overload + p_fatigue)
        dominant_idx = int(np.argmax(posterior))

        return HMMStateEstimate(
            student_id=self.student_id,
            timestamp=timestamp or datetime.utcnow(),
            p_underload=float(p_underload),
            p_flow=float(p_flow),
            p_overload=float(p_overload),
            p_fatigue=float(p_fatigue),
            dominant_state=CognitiveState.from_index(dominant_idx),
            iori=iori,
            risk_zone=classify_risk_zone(iori),
            observation_vector={
                'rho': observation.rho,
                'rho_bin': observation.rho_bin,
                **observation.raw_features,
            },
            is_provisional_params=self.params.is_provisional,
            model_version=self.params.version,
        )

    def reset(self):
        """Reset filter to initial state distribution (start of new session)."""
        self.alpha_hat = self.params.pi.copy()
        self.log_likelihood = 0.0
        self.step_count = 0


def run_batch_forward_filter(
    student_id: str,
    rho_series: list[float],
    params: Optional[HMMParameters] = None,
    timestamps: Optional[list[datetime]] = None,
) -> list[HMMStateEstimate]:
    """
    Run the forward filter over a complete historical rho series.
    Returns one HMMStateEstimate per time step.

    This is CAUSAL: each estimate uses only observations up to that point.
    """
    hmm = RealTimeHMMFilter(student_id=student_id, params=params)
    estimates = []

    for t, rho in enumerate(rho_series):
        obs_bin = discretise_rho(rho)
        obs = ObservationVector(
            rho=rho,
            rho_bin=obs_bin,
            raw_features={'step': t},
        )
        ts = timestamps[t] if timestamps else datetime.utcnow()
        estimate = hmm.current_estimate(obs, timestamp=ts)
        estimates.append(estimate)

    return estimates

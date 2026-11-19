"""
Model 2: M/M/1 Queueing Workload Assessment
============================================
Compares a student's incoming weighted academic workload (lambda) against
their estimated cognitive processing capacity (mu = C) using M/M/1 queueing
theory.

Queue metrics
-------------
  rho  = lambda / mu               (utilization / cognitive load ratio)
  L    = rho / (1 - rho)           (expected backlog; ONLY valid when rho < 1)
  W    = 1 / (mu - lambda)         (expected assimilation latency; ONLY valid when rho < 1)

Stability condition: rho < 1  <=>  lambda < mu
If lambda >= mu, the queue is UNSTABLE. L and W are undefined (not silently
computed as finite numbers).

Cognitive regime interpretation
--------------------------------
  rho < 0.50          : Underload / under-stimulation
  0.50 <= rho <= 0.80 : Flow (optimal)
  0.80 < rho < 1.00   : Cognitive strain (backlog grows non-linearly)
  rho >= 1.00         : Overload / thrashing (queue unstable)

Limitations (MUST be communicated to users)
--------------------------------------------
1. Poisson arrival assumption is an approximation for academic workload.
2. Exponential service-time assumption does not capture learning heterogeneity.
3. The M/M/1 model assumes a memoryless process; real cognitive processing
   has memory and temporal dependencies.
4. Results are risk indicators, not exact predictions of student performance.
5. The composite ICAP workload weight is a research proxy for cognitive demand,
   not a direct measurement of processing time.
6. The capacity estimate carries Bayesian uncertainty (credible interval);
   using the posterior mean as mu ignores this uncertainty.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from enum import Enum


class CognitiveRegime(str, Enum):
    UNDERLOAD = 'underload'
    FLOW      = 'flow'
    STRAIN    = 'strain'
    OVERLOAD  = 'overload'  # Queue unstable


@dataclass
class QueueMetrics:
    """M/M/1 queue metrics for a student on a given day."""
    student_id: str
    date: date
    lambda_demand: float          # Smoothed incoming workload (from Model 3)
    mu_capacity: float            # Cognitive capacity posterior mean (from Model 1)
    rho: float                    # Utilization ratio
    L: Optional[float]            # Expected queue length (None if unstable)
    W: Optional[float]            # Expected wait time (None if unstable)
    is_stable: bool               # False if lambda >= mu
    instability_reason: Optional[str]
    cognitive_regime: CognitiveRegime
    model_version: str
    calculated_at: datetime

    # Documented limitations are always attached to the output
    limitations: Optional[list[str]] = None

    def __post_init__(self):
        if self.limitations is None:
            self.limitations = [
                'Poisson arrival is an approximation for academic workloads',
                'Exponential service-time does not capture learning heterogeneity',
                'Results are support indicators, not exact performance predictions',
                'Capacity estimate carries Bayesian uncertainty not reflected in rho',
            ]


def classify_regime(rho: float, is_stable: bool) -> CognitiveRegime:
    """Map utilization ratio to a cognitive regime label."""
    if not is_stable or rho >= 1.0:
        return CognitiveRegime.OVERLOAD
    elif rho < 0.50:
        return CognitiveRegime.UNDERLOAD
    elif rho <= 0.80:
        return CognitiveRegime.FLOW
    else:
        return CognitiveRegime.STRAIN


def calculate_queue_metrics(
    student_id: str,
    lambda_demand: float,
    mu_capacity: float,
    observation_date: date,
    model_version: str = 'v1.0',
) -> QueueMetrics:
    """
    Calculate M/M/1 queue metrics for a student.

    Parameters
    ----------
    student_id       : student UUID
    lambda_demand    : smoothed incoming workload (from Model 3)
    mu_capacity      : cognitive capacity posterior mean (from Model 1)
    observation_date : date of calculation
    model_version    : for audit traceability

    Returns
    -------
    QueueMetrics with all computed values, or instability flags if rho >= 1
    """
    if mu_capacity <= 0.0:
        return QueueMetrics(
            student_id=student_id,
            date=observation_date,
            lambda_demand=lambda_demand,
            mu_capacity=mu_capacity,
            rho=float('inf'),
            L=None,
            W=None,
            is_stable=False,
            instability_reason='Capacity estimate is zero or negative; cannot compute queue metrics.',
            cognitive_regime=CognitiveRegime.OVERLOAD,
            model_version=model_version,
            calculated_at=datetime.utcnow(),
        )

    rho = lambda_demand / mu_capacity

    # Stability check: rho must be strictly < 1
    if rho >= 1.0:
        return QueueMetrics(
            student_id=student_id,
            date=observation_date,
            lambda_demand=lambda_demand,
            mu_capacity=mu_capacity,
            rho=rho,
            L=None,   # UNDEFINED — queue unstable
            W=None,   # UNDEFINED — queue unstable
            is_stable=False,
            instability_reason=(
                f'Queue unstable: lambda ({lambda_demand:.4f}) >= mu ({mu_capacity:.4f}). '
                f'rho = {rho:.4f}. L and W are undefined for an unstable queue.'
            ),
            cognitive_regime=CognitiveRegime.OVERLOAD,
            model_version=model_version,
            calculated_at=datetime.utcnow(),
        )

    # Stable queue: compute M/M/1 metrics
    # L = rho / (1 - rho)  = E[number in system]
    # W = 1 / (mu - lambda) = E[time in system]
    L = rho / (1.0 - rho)
    W = 1.0 / (mu_capacity - lambda_demand)

    return QueueMetrics(
        student_id=student_id,
        date=observation_date,
        lambda_demand=lambda_demand,
        mu_capacity=mu_capacity,
        rho=rho,
        L=L,
        W=W,
        is_stable=True,
        instability_reason=None,
        cognitive_regime=classify_regime(rho, is_stable=True),
        model_version=model_version,
        calculated_at=datetime.utcnow(),
    )

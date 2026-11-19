"""
Model 3: ICAP-Weighted Incoming Workload Quantification
========================================================
Quantifies the incoming academic workload for each student by applying
ICAPP-grounded activity weights to observed learning events, then smoothing
with a three-day causal moving average.

ICAPP Framework reference: Chi & Wylie (2014)
  Interactive > Constructive > Active > Passive

Activity weights are stored in activity_weight_configs and versioned.
All weights below are explicitly marked PROVISIONAL until validated
by the research methodology.

Three-day causal moving average (uses only past observations):
  lambda_bar(i,t) = [lambda(i,t) + lambda(i,t-1) + lambda(i,t-2)] / 3

Workload categories are kept separate:
  incoming    - tasks assigned but not yet started
  active      - tasks currently being worked on
  completed   - tasks finished
  overdue     - tasks past due date and not completed
  ineffective - interactions that do not contribute to learning progress
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
import numpy as np


# ---------------------------------------------------------------------------
# PROVISIONAL ICAP activity weight registry
# These are stored in the database (activity_weight_configs) and must be
# loaded from there at runtime. This dict is the PROVISIONAL seed default.
# ---------------------------------------------------------------------------
PROVISIONAL_WEIGHTS: dict[str, float] = {
    # Passive ICAP level
    'navigate':            0.10,  # PROVISIONAL
    'open_resource':       0.20,  # PROVISIONAL
    'watch_video':         0.50,  # PROVISIONAL
    # Active ICAP level
    'read_pdf':            0.80,  # PROVISIONAL
    'take_notes':          1.00,  # PROVISIONAL
    'download':            0.30,  # PROVISIONAL
    # Constructive ICAP level
    'attempt_quiz':        2.00,  # PROVISIONAL
    'complete_assignment': 3.00,  # PROVISIONAL
    # Interactive ICAP level
    'prepare_project':     4.00,  # PROVISIONAL
    'submit_assessment':   5.00,  # PROVISIONAL
    # Session events (minimal workload)
    'login':               0.05,  # PROVISIONAL
    'logout':              0.00,  # PROVISIONAL
}

ICAPP_LEVELS: dict[str, str] = {
    'navigate':            'passive',
    'open_resource':       'passive',
    'watch_video':         'passive',
    'read_pdf':            'active',
    'take_notes':          'active',
    'download':            'active',
    'attempt_quiz':        'constructive',
    'complete_assignment': 'constructive',
    'prepare_project':     'interactive',
    'submit_assessment':   'interactive',
    'login':               'passive',
    'logout':              'passive',
}


@dataclass
class DailyActivitySummary:
    """Aggregated activity counts for a single student on a single day."""
    student_id: str
    date: date
    event_counts: dict[str, int]  # event_type -> count
    weight_config_version: str = 'v1.0-provisional'


@dataclass
class WorkloadObservation:
    """Model 3 output for a single student on a single day."""
    student_id: str
    date: date
    raw_lambda: float            # Weighted sum of events that day
    smoothed_lambda: float       # 3-day causal moving average
    incoming_workload: float     # Tasks assigned but not started
    active_workload: float       # Tasks in progress
    completed_workload: float    # Tasks finished
    overdue_workload: float      # Tasks past due, unfinished
    ineffective_interactions: float  # Interactions not contributing to learning
    weight_config_version: str
    model_version: str
    calculated_at: datetime


def calculate_daily_weighted_lambda(
    event_counts: dict[str, int],
    weights: Optional[dict[str, float]] = None,
) -> float:
    """
    Calculate raw daily weighted workload lambda.

    lambda(i,t) = sum_k [ w_k * count_k ]

    where w_k is the ICAP weight for activity type k.

    Parameters
    ----------
    event_counts : dict mapping event_type to count for the day
    weights      : ICAP weight registry (defaults to PROVISIONAL_WEIGHTS)

    Returns
    -------
    float : raw weighted lambda for the day
    """
    if weights is None:
        weights = PROVISIONAL_WEIGHTS

    total = 0.0
    for event_type, count in event_counts.items():
        w = weights.get(event_type, 0.0)
        total += w * count
    return total


def apply_causal_moving_average(
    lambda_series: list[float],
    window: int = 3,
) -> list[float]:
    """
    Apply a causal (backward-looking) moving average over the lambda series.

    lambda_bar(t) = [lambda(t) + lambda(t-1) + ... + lambda(t-window+1)] / window

    Uses only past and current observations. Never uses future observations.
    For the first few days where fewer than `window` observations exist,
    the average is computed over available observations only (partial window).

    Parameters
    ----------
    lambda_series : list of raw daily lambda values in chronological order
    window        : moving average window (default 3 days per approved formula)

    Returns
    -------
    list of smoothed lambda values, same length as input
    """
    smoothed = []
    for t in range(len(lambda_series)):
        start = max(0, t - window + 1)
        window_values = lambda_series[start:t + 1]
        smoothed.append(float(np.mean(window_values)))
    return smoothed


def calculate_workload_observations(
    student_id: str,
    daily_summaries: list[DailyActivitySummary],
    task_workloads: Optional[dict[str, dict[str, float]]] = None,
    weights: Optional[dict[str, float]] = None,
    model_version: str = 'v1.0-provisional',
) -> list[WorkloadObservation]:
    """
    Calculate Model 3 workload observations for all days in the history.

    Parameters
    ----------
    student_id      : student UUID
    daily_summaries : chronologically ordered list of daily activity summaries
    task_workloads  : optional dict of date_str -> {incoming, active, completed, overdue}
                      workload contributions from academic tasks
    weights         : ICAP weight registry (defaults to PROVISIONAL_WEIGHTS)
    model_version   : for audit traceability

    Returns
    -------
    list of WorkloadObservation, one per day
    """
    if weights is None:
        weights = PROVISIONAL_WEIGHTS
    if task_workloads is None:
        task_workloads = {}

    # Sort by date (defensive)
    summaries = sorted(daily_summaries, key=lambda s: s.date)

    # Calculate raw lambda for each day
    raw_lambdas = [
        calculate_daily_weighted_lambda(s.event_counts, weights)
        for s in summaries
    ]

    # Apply 3-day causal moving average
    smoothed_lambdas = apply_causal_moving_average(raw_lambdas, window=3)

    observations = []
    for i, summary in enumerate(summaries):
        date_str = summary.date.isoformat()
        tw = task_workloads.get(date_str, {})

        # Estimate ineffective interactions: events with weight 0 or login/logout
        ineffective = sum(
            count for etype, count in summary.event_counts.items()
            if weights.get(etype, 0.0) < 0.1
        ) * 0.05  # Minimal contribution

        obs = WorkloadObservation(
            student_id=student_id,
            date=summary.date,
            raw_lambda=raw_lambdas[i],
            smoothed_lambda=smoothed_lambdas[i],
            incoming_workload=tw.get('incoming', 0.0),
            active_workload=tw.get('active', 0.0),
            completed_workload=tw.get('completed', 0.0),
            overdue_workload=tw.get('overdue', 0.0),
            ineffective_interactions=ineffective,
            weight_config_version=summary.weight_config_version,
            model_version=model_version,
            calculated_at=datetime.utcnow(),
        )
        observations.append(obs)

    return observations

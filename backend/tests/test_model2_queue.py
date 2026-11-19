"""
Unit tests for Model 2: M/M/1 Queueing Workload Assessment.
"""

from datetime import date
import pytest

from app.analytics.model2_queue import (
    CognitiveRegime,
    QueueMetrics,
    classify_regime,
    calculate_queue_metrics,
)


def test_stable_queue_metrics():
    """Given lambda < mu, verify rho, L, and W formulas for an M/M/1 queue."""
    obs_date = date(2026, 11, 19)
    lambda_demand = 6.0
    mu_capacity = 10.0

    metrics = calculate_queue_metrics(
        student_id="student-queue-stable",
        lambda_demand=lambda_demand,
        mu_capacity=mu_capacity,
        observation_date=obs_date,
    )

    expected_rho = 6.0 / 10.0  # 0.60
    expected_L = expected_rho / (1.0 - expected_rho)  # 0.6 / 0.4 = 1.5
    expected_W = 1.0 / (mu_capacity - lambda_demand)  # 1.0 / 4.0 = 0.25

    assert metrics.is_stable is True
    assert metrics.instability_reason is None
    assert metrics.rho == pytest.approx(expected_rho)
    assert metrics.L == pytest.approx(expected_L)
    assert metrics.W == pytest.approx(expected_W)
    assert metrics.cognitive_regime == CognitiveRegime.FLOW


def test_unstable_queue_L_is_none():
    """When lambda >= mu, L and W must be None (undefined for unstable queues)."""
    obs_date = date(2026, 11, 19)

    # Exactly at capacity boundary: lambda == mu
    metrics_boundary = calculate_queue_metrics(
        student_id="student-boundary",
        lambda_demand=10.0,
        mu_capacity=10.0,
        observation_date=obs_date,
    )
    assert metrics_boundary.is_stable is False
    assert metrics_boundary.L is None
    assert metrics_boundary.W is None
    assert metrics_boundary.rho == pytest.approx(1.0)

    # Over capacity: lambda > mu
    metrics_over = calculate_queue_metrics(
        student_id="student-over",
        lambda_demand=15.0,
        mu_capacity=10.0,
        observation_date=obs_date,
    )
    assert metrics_over.is_stable is False
    assert metrics_over.L is None
    assert metrics_over.W is None
    assert metrics_over.rho == pytest.approx(1.5)


def test_unstable_queue_is_stable_false():
    """Verify is_stable is False when lambda >= mu and instability_reason is descriptive."""
    obs_date = date(2026, 11, 19)
    metrics = calculate_queue_metrics(
        student_id="student-unstable",
        lambda_demand=12.0,
        mu_capacity=10.0,
        observation_date=obs_date,
    )

    assert metrics.is_stable is False
    assert metrics.instability_reason is not None
    assert "Queue unstable" in metrics.instability_reason
    assert "lambda (12.0000) >= mu (10.0000)" in metrics.instability_reason
    assert metrics.cognitive_regime == CognitiveRegime.OVERLOAD


def test_regime_classification():
    """Verify correct CognitiveRegime assignment across all rho ranges."""
    # Underload: rho < 0.50
    assert classify_regime(0.0, is_stable=True) == CognitiveRegime.UNDERLOAD
    assert classify_regime(0.25, is_stable=True) == CognitiveRegime.UNDERLOAD
    assert classify_regime(0.499, is_stable=True) == CognitiveRegime.UNDERLOAD

    # Flow: 0.50 <= rho <= 0.80
    assert classify_regime(0.50, is_stable=True) == CognitiveRegime.FLOW
    assert classify_regime(0.65, is_stable=True) == CognitiveRegime.FLOW
    assert classify_regime(0.80, is_stable=True) == CognitiveRegime.FLOW

    # Strain: 0.80 < rho < 1.00
    assert classify_regime(0.801, is_stable=True) == CognitiveRegime.STRAIN
    assert classify_regime(0.95, is_stable=True) == CognitiveRegime.STRAIN
    assert classify_regime(0.999, is_stable=True) == CognitiveRegime.STRAIN

    # Overload: rho >= 1.0 or not is_stable
    assert classify_regime(1.0, is_stable=False) == CognitiveRegime.OVERLOAD
    assert classify_regime(1.5, is_stable=False) == CognitiveRegime.OVERLOAD
    assert classify_regime(0.7, is_stable=False) == CognitiveRegime.OVERLOAD


def test_zero_capacity_handled():
    """mu=0 or mu < 0 must be handled gracefully without ZeroDivisionError."""
    obs_date = date(2026, 11, 19)

    # mu == 0
    metrics_zero = calculate_queue_metrics(
        student_id="student-mu-zero",
        lambda_demand=5.0,
        mu_capacity=0.0,
        observation_date=obs_date,
    )
    assert metrics_zero.is_stable is False
    assert metrics_zero.rho == float("inf")
    assert metrics_zero.L is None
    assert metrics_zero.W is None
    assert metrics_zero.cognitive_regime == CognitiveRegime.OVERLOAD
    assert "Capacity estimate is zero or negative" in metrics_zero.instability_reason

    # mu < 0
    metrics_neg = calculate_queue_metrics(
        student_id="student-mu-neg",
        lambda_demand=5.0,
        mu_capacity=-2.0,
        observation_date=obs_date,
    )
    assert metrics_neg.is_stable is False
    assert metrics_neg.L is None
    assert metrics_neg.W is None


def test_limitations_always_present():
    """QueueMetrics must always attach documented mathematical limitations."""
    obs_date = date(2026, 11, 19)
    metrics_stable = calculate_queue_metrics("s1", 5.0, 10.0, obs_date)
    assert isinstance(metrics_stable.limitations, list)
    assert len(metrics_stable.limitations) >= 4
    assert any("Poisson arrival" in lim for lim in metrics_stable.limitations)

    metrics_unstable = calculate_queue_metrics("s2", 15.0, 10.0, obs_date)
    assert isinstance(metrics_unstable.limitations, list)
    assert len(metrics_unstable.limitations) >= 4

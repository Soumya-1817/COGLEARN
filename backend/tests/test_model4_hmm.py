"""
Unit tests for Model 4: Four-State Hidden Markov Model for Cognitive State Estimation.
"""

from datetime import datetime
import pytest
import numpy as np

from app.analytics.model4_hmm import (
    CognitiveState,
    RiskZone,
    IORI_THRESHOLDS,
    PROVISIONAL_PI,
    PROVISIONAL_A,
    PROVISIONAL_B,
    HMMParameters,
    ObservationVector,
    HMMStateEstimate,
    discretise_rho,
    classify_risk_zone,
    RealTimeHMMFilter,
    run_batch_forward_filter,
)


def test_initial_belief_equals_pi():
    """Before any observation update, initial belief must match pi distribution."""
    params = HMMParameters.provisional_default()
    filter_ = RealTimeHMMFilter(student_id="student-init", params=params)

    assert np.allclose(filter_.alpha_hat, params.pi)
    assert filter_.step_count == 0
    assert filter_.log_likelihood == 0.0


def test_posterior_sums_to_one():
    """After every forward filter update, posterior probabilities must sum to 1.0."""
    filter_ = RealTimeHMMFilter(student_id="student-sum")
    test_rhos = [0.1, 0.45, 0.65, 0.95, 1.3, 0.2]

    for step, rho in enumerate(test_rhos):
        obs = ObservationVector(rho=rho, rho_bin=discretise_rho(rho), raw_features={'step': step})
        posterior = filter_.update(obs)
        assert np.isclose(posterior.sum(), 1.0, atol=1e-6)
        assert np.all(posterior >= 0.0)


def test_iori_range():
    """IORI = P(Overload) + P(Fatigue) must always lie strictly within [0.0, 1.0]."""
    filter_ = RealTimeHMMFilter(student_id="student-iori")
    test_rhos = [0.0, 0.2, 0.6, 0.9, 1.1, 1.8, 0.1, 0.4]

    for step, rho in enumerate(test_rhos):
        obs = ObservationVector(rho=rho, rho_bin=discretise_rho(rho), raw_features={'step': step})
        est = filter_.current_estimate(obs)
        assert 0.0 <= est.iori <= 1.0
        assert np.isclose(est.iori, est.p_overload + est.p_fatigue, atol=1e-6)
        assert est.risk_zone in (RiskZone.GREEN, RiskZone.YELLOW, RiskZone.RED)


def test_causal_filtering():
    """
    Causal forward filtering: estimate at time t must depend only on
    observations up to t, and is unaffected by future observations.
    """
    rho_prefix = [0.2, 0.7, 0.5]
    rho_full_a = rho_prefix + [0.1, 0.2]
    rho_full_b = rho_prefix + [1.5, 1.8]

    estimates_a = run_batch_forward_filter("student-causal", rho_full_a)
    estimates_b = run_batch_forward_filter("student-causal", rho_full_b)

    # For steps 0, 1, 2, the estimates must be identical despite divergent futures
    for t in range(len(rho_prefix)):
        np.testing.assert_allclose(estimates_a[t].posterior, estimates_b[t].posterior, atol=1e-9)
        assert estimates_a[t].dominant_state == estimates_b[t].dominant_state
        assert pytest.approx(estimates_a[t].iori) == estimates_b[t].iori


def test_degenerate_observation_fallback():
    """Zero-emission observation should trigger safe fallback to uniform belief without crashing."""
    params = HMMParameters.provisional_default()
    # Create emission matrix where one symbol has zero probability across all states
    zero_emission_B = params.B.copy()
    zero_emission_B[:, 0] = 0.0  # All states have 0 probability of observing symbol 0
    # Normalize other columns to maintain row sums
    for row in range(4):
        zero_emission_B[row] /= zero_emission_B[row].sum()

    custom_params = HMMParameters(
        pi=params.pi.copy(),
        A=params.A.copy(),
        B=zero_emission_B,
    )

    filter_ = RealTimeHMMFilter(student_id="student-degen", params=custom_params)
    obs = ObservationVector(rho=0.1, rho_bin=0, raw_features={})
    posterior = filter_.update(obs)

    # Fallback to uniform distribution: 1/4 = 0.25 each
    assert np.allclose(posterior, np.array([0.25, 0.25, 0.25, 0.25]))


def test_risk_zone_thresholds():
    """Verify green/yellow/red risk zone boundaries at 0.30 and 0.60."""
    # Green: IORI < 0.30
    assert classify_risk_zone(0.0) == RiskZone.GREEN
    assert classify_risk_zone(0.15) == RiskZone.GREEN
    assert classify_risk_zone(0.299) == RiskZone.GREEN

    # Yellow: 0.30 <= IORI < 0.60
    assert classify_risk_zone(0.30) == RiskZone.YELLOW
    assert classify_risk_zone(0.45) == RiskZone.YELLOW
    assert classify_risk_zone(0.599) == RiskZone.YELLOW

    # Red: IORI >= 0.60
    assert classify_risk_zone(0.60) == RiskZone.RED
    assert classify_risk_zone(0.85) == RiskZone.RED
    assert classify_risk_zone(1.0) == RiskZone.RED


def test_batch_forward_filter_length():
    """run_batch_forward_filter returns exactly one estimate per input rho."""
    rho_series = [0.2, 0.4, 0.6, 0.8, 1.2, 0.5]
    estimates = run_batch_forward_filter(
        student_id="student-batch",
        rho_series=rho_series,
    )
    assert len(estimates) == len(rho_series)
    assert all(isinstance(e, HMMStateEstimate) for e in estimates)


def test_hmm_parameter_validation():
    """Invalid transition or emission matrices must raise AssertionError during validation."""
    valid_params = HMMParameters.provisional_default()

    # Invalid A row sum
    bad_A = valid_params.A.copy()
    bad_A[0, 0] = 0.99  # Row 0 sum != 1.0
    bad_params = HMMParameters(pi=valid_params.pi.copy(), A=bad_A, B=valid_params.B.copy())
    with pytest.raises(AssertionError, match="A rows must sum to 1"):
        bad_params.validate()

    # Invalid pi sum
    bad_pi = np.array([0.2, 0.2, 0.2, 0.2])  # sum = 0.8
    bad_pi_params = HMMParameters(pi=bad_pi, A=valid_params.A.copy(), B=valid_params.B.copy())
    with pytest.raises(AssertionError, match="pi must sum to 1"):
        bad_pi_params.validate()

    # Invalid B shape
    bad_B = np.zeros((3, 5))
    bad_B_params = HMMParameters(pi=valid_params.pi.copy(), A=valid_params.A.copy(), B=bad_B)
    with pytest.raises(AssertionError, match="B state dimension mismatch"):
        bad_B_params.validate()


def test_discretise_rho():
    """Verify binning logic of utilization ratio into discrete observation indices."""
    assert discretise_rho(-0.5) == 0  # clamped to 0 -> bin 0
    assert discretise_rho(0.0) == 0
    assert discretise_rho(0.29) == 0
    assert discretise_rho(0.30) == 1
    assert discretise_rho(0.49) == 1
    assert discretise_rho(0.50) == 2
    assert discretise_rho(0.79) == 2
    assert discretise_rho(0.80) == 3
    assert discretise_rho(0.99) == 3
    assert discretise_rho(1.00) == 4
    assert discretise_rho(2.50) == 4


def test_filter_reset():
    """Resetting filter must restore alpha_hat back to prior pi."""
    filter_ = RealTimeHMMFilter(student_id="student-reset")
    filter_.update(ObservationVector(rho=1.2, rho_bin=4, raw_features={}))
    assert not np.allclose(filter_.alpha_hat, filter_.params.pi)

    filter_.reset()
    assert np.allclose(filter_.alpha_hat, filter_.params.pi)
    assert filter_.step_count == 0
    assert filter_.log_likelihood == 0.0

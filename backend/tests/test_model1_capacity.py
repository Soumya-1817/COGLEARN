"""
Unit tests for Model 1: Hierarchical Bayesian Cognitive Capacity Estimation.
"""

import pytest
import numpy as np

from app.analytics.model1_capacity import (
    DEFAULT_ALPHA_0,
    DEFAULT_BETA_0,
    ANOMALY_ZSCORE_THRESHOLD,
    CapacityPrior,
    CapacityEstimate,
    detect_anomalies,
    update_posterior,
    estimate_capacity,
    update_cohort_prior_empirical_bayes,
)


def test_cold_start_returns_prior():
    """When no observations exist (cold start), estimate must match prior mean."""
    student_id = "student-cold-start"
    estimate = estimate_capacity(student_id=student_id, daily_counts=[])

    assert estimate.student_id == student_id
    assert estimate.alpha_post == DEFAULT_ALPHA_0
    assert estimate.beta_post == DEFAULT_BETA_0
    assert estimate.mean_capacity == pytest.approx(DEFAULT_ALPHA_0 / DEFAULT_BETA_0)
    assert estimate.variance == pytest.approx(DEFAULT_ALPHA_0 / (DEFAULT_BETA_0 ** 2))
    assert estimate.n_observations == 0
    assert estimate.n_anomalous_excluded == 0
    assert estimate.is_provisional_params is True
    assert estimate.ci_lower_95 < estimate.mean_capacity < estimate.ci_upper_95


def test_posterior_update_correctness():
    """Given known counts, verify alpha_post, beta_post, and posterior statistics."""
    prior = CapacityPrior(alpha_0=2.0, beta_0=1.0)
    counts = [10.0, 12.0, 11.0]  # homogeneous counts, no anomalies
    alpha_post, beta_post, n_valid, n_anomalous = update_posterior(prior, counts)

    assert n_valid == 3
    assert n_anomalous == 0
    assert alpha_post == pytest.approx(2.0 + sum(counts))  # 35.0
    assert beta_post == pytest.approx(1.0 + 3)             # 4.0

    estimate = estimate_capacity(
        student_id="student-update-test",
        daily_counts=counts,
        prior=prior,
    )
    expected_mean = 35.0 / 4.0
    expected_var = 35.0 / (4.0 ** 2)
    assert estimate.mean_capacity == pytest.approx(expected_mean)
    assert estimate.variance == pytest.approx(expected_var)
    assert estimate.n_observations == 3
    assert estimate.n_anomalous_excluded == 0


def test_anomaly_detection_excludes_spikes():
    """Spurious high counts exceeding z-score threshold must be flagged and excluded."""
    # 25 observations around 10.0, plus an extreme spike of 500.0
    normal_counts = [10.0, 10.5, 9.8, 10.2, 10.1] * 5
    spike = [500.0]
    all_counts = normal_counts + spike

    valid_counts, anomaly_indices = detect_anomalies(all_counts, threshold_zscore=3.5)

    assert len(anomaly_indices) == 1
    assert anomaly_indices[0] == 25
    assert valid_counts == normal_counts

    estimate = estimate_capacity(
        student_id="student-spike-test",
        daily_counts=all_counts,
    )
    assert estimate.n_anomalous_excluded == 1
    assert estimate.n_observations == len(normal_counts)
    # The mean capacity should not be blown up by 500.0
    assert estimate.mean_capacity < 15.0


def test_anomaly_detection_edge_cases():
    """Test anomaly detection behavior with fewer than 3 observations or zero variance."""
    # Fewer than 3 observations
    counts_short = [10.0, 20.0]
    valid, anom = detect_anomalies(counts_short)
    assert valid == counts_short
    assert anom == []

    # Zero standard deviation
    counts_identical = [5.0, 5.0, 5.0, 5.0]
    valid, anom = detect_anomalies(counts_identical)
    assert valid == counts_identical
    assert anom == []


def test_credible_interval_contains_mean():
    """95% credible interval [ci_lower, ci_upper] must strictly bracket the posterior mean."""
    for counts in [[], [5.0], [12.0, 14.0, 13.0, 15.0], [50.0] * 10]:
        estimate = estimate_capacity(student_id="student-ci-test", daily_counts=counts)
        assert estimate.ci_lower_95 < estimate.mean_capacity < estimate.ci_upper_95
        assert estimate.uncertainty_width > 0.0


def test_uncertainty_decreases_with_observations():
    """As more valid daily observations are gathered, estimation uncertainty must monotonically decrease."""
    est_0 = estimate_capacity("s-unc", [])
    est_5 = estimate_capacity("s-unc", [2.0] * 5)
    est_20 = estimate_capacity("s-unc", [2.0] * 20)
    est_50 = estimate_capacity("s-unc", [2.0] * 50)

    assert est_0.uncertainty_width > est_5.uncertainty_width > est_20.uncertainty_width > est_50.uncertainty_width
    assert est_0.variance > est_5.variance > est_20.variance > est_50.variance

    # Also verify monotonic decrease for higher activity rates as observations increase
    est_hi_5 = estimate_capacity("s-hi", [15.0] * 5)
    est_hi_20 = estimate_capacity("s-hi", [15.0] * 20)
    est_hi_50 = estimate_capacity("s-hi", [15.0] * 50)
    assert est_hi_5.uncertainty_width > est_hi_20.uncertainty_width > est_hi_50.uncertainty_width
    assert est_hi_5.variance > est_hi_20.variance > est_hi_50.variance


def test_shrinkage_property():
    """
    Bayesian shrinkage:
    For small n, estimate is shrunk towards prior alpha_0 / beta_0.
    For large n, estimate converges to the sample mean sum(x_i)/n.
    """
    prior = CapacityPrior(alpha_0=2.0, beta_0=1.0)  # prior mean = 2.0
    empirical_rate = 25.0

    # n = 1: (2 + 25) / (1 + 1) = 13.5
    est_1 = estimate_capacity("s-shrink", [empirical_rate], prior=prior)
    assert est_1.mean_capacity == pytest.approx(13.5)

    # n = 5: (2 + 125) / (1 + 5) = 127/6 ≈ 21.17
    est_5 = estimate_capacity("s-shrink", [empirical_rate] * 5, prior=prior)
    assert 2.0 < est_1.mean_capacity < est_5.mean_capacity < empirical_rate

    # n = 100: (2 + 2500) / (1 + 100) = 2502/101 ≈ 24.77
    est_100 = estimate_capacity("s-shrink", [empirical_rate] * 100, prior=prior)
    assert abs(est_100.mean_capacity - empirical_rate) < 0.3


def test_empirical_bayes_cohort_prior():
    """Test Empirical Bayes Method of Moments hyperprior estimation."""
    # Insufficient cohort (< 5 students)
    small_cohort = [[10.0, 12.0]] * 4
    prior_small = update_cohort_prior_empirical_bayes(small_cohort)
    assert prior_small.is_provisional is True
    assert prior_small.alpha_0 == DEFAULT_ALPHA_0

    # Sufficient cohort but < 30 students -> updated parameters, still provisional
    mid_cohort = [[10.0 + i % 3] * 5 for i in range(15)]
    prior_mid = update_cohort_prior_empirical_bayes(mid_cohort)
    assert prior_mid.is_provisional is True
    assert prior_mid.alpha_0 > 0.0
    assert prior_mid.beta_0 > 0.0

    # Cohort >= 30 students -> non-provisional v1.1
    large_cohort = [[10.0 + (i % 5) * 2] * 7 for i in range(35)]
    prior_large = update_cohort_prior_empirical_bayes(large_cohort)
    assert prior_large.is_provisional is False
    assert prior_large.version == 'v1.1-empirical-bayes'
    assert prior_large.prior_mean > 0.0

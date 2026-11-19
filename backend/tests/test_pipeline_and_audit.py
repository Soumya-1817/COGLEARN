"""
Unit tests for Pipeline and Audit log formatting.
"""

from datetime import date
import pytest

from app.analytics.model1_capacity import CapacityPrior
from app.analytics.model3_workload import DailyActivitySummary
from app.analytics.pipeline import run_full_pipeline_for_student
from app.analytics.audit import (
    make_model1_audit,
    make_model2_audit,
    make_model3_audit,
    make_model4_audit,
)


def test_full_pipeline_happy_path():
    """Verify that run_full_pipeline_for_student executes all four models end-to-end."""
    student_id = "pipeline-student-1"
    summaries = [
        DailyActivitySummary(
            student_id=student_id,
            date=date(2026, 11, 15),
            event_counts={'read_pdf': 2, 'attempt_quiz': 1},
        ),
        DailyActivitySummary(
            student_id=student_id,
            date=date(2026, 11, 16),
            event_counts={'watch_video': 3, 'take_notes': 2},
        ),
        DailyActivitySummary(
            student_id=student_id,
            date=date(2026, 11, 17),
            event_counts={'prepare_project': 1, 'submit_assessment': 1},
        ),
    ]

    result = run_full_pipeline_for_student(
        student_id=student_id,
        daily_summaries=summaries,
    )

    assert result['student_id'] == student_id
    assert result['errors'] == []
    assert result['capacity_estimate'] is not None
    assert result['capacity_estimate'].mean_capacity > 0.0
    assert len(result['workload_observations']) == 3
    assert len(result['queue_metrics']) == 3
    assert len(result['hmm_estimates']) == 3

    latest_hmm = result['hmm_estimates'][-1]
    assert 0.0 <= latest_hmm.iori <= 1.0


def test_pipeline_resilience_on_empty_summaries():
    """Empty daily summaries should not crash the pipeline; cold-start estimate is computed."""
    result = run_full_pipeline_for_student(
        student_id="empty-student",
        daily_summaries=[],
    )

    assert result['student_id'] == "empty-student"
    assert result['errors'] == []
    assert result['capacity_estimate'] is not None
    assert result['capacity_estimate'].n_observations == 0
    assert result['workload_observations'] == []
    assert result['queue_metrics'] == []
    assert result['hmm_estimates'] == []


def test_audit_helpers():
    """Verify audit record formatting functions produce expected structures."""
    m1_audit = make_model1_audit(
        student_id="s1",
        model_version_id="v1.0",
        alpha_prior=2.0,
        beta_prior=1.0,
        daily_counts_used=[10.0, 12.0],
        n_anomalous_excluded=0,
        alpha_post=24.0,
        beta_post=3.0,
        mean_capacity=8.0,
        ci_lower=5.0,
        ci_upper=11.0,
        duration_ms=1.5,
    )
    assert m1_audit['model_number'] == 1
    assert m1_audit['output_data']['mean_capacity'] == 8.0

    m2_audit = make_model2_audit(
        student_id="s1",
        model_version_id="v1.0",
        lambda_demand=5.0,
        mu_capacity=10.0,
        rho=0.5,
        L=1.0,
        W=0.2,
        is_stable=True,
        duration_ms=0.8,
    )
    assert m2_audit['model_number'] == 2
    assert m2_audit['output_data']['is_stable'] is True

    m3_audit = make_model3_audit(
        student_id="s1",
        model_version_id="v1.0",
        date="2026-11-19",
        event_counts={'read_pdf': 2},
        weight_config_version="v1.0",
        raw_lambda=1.6,
        smoothed_lambda=1.6,
        duration_ms=0.5,
    )
    assert m3_audit['model_number'] == 3
    assert m3_audit['output_data']['raw_lambda'] == 1.6

    m4_audit = make_model4_audit(
        student_id="s1",
        model_version_id="v1.0",
        rho_bin=2,
        rho=0.6,
        p_underload=0.1,
        p_flow=0.7,
        p_overload=0.15,
        p_fatigue=0.05,
        iori=0.20,
        risk_zone="green",
        is_provisional=True,
        duration_ms=1.2,
    )
    assert m4_audit['model_number'] == 4
    assert m4_audit['output_data']['risk_zone'] == "green"

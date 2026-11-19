"""
Unit tests for Model 3: ICAP-Weighted Incoming Workload Quantification.
"""

from datetime import date
import pytest

from app.analytics.model3_workload import (
    PROVISIONAL_WEIGHTS,
    ICAPP_LEVELS,
    DailyActivitySummary,
    WorkloadObservation,
    calculate_daily_weighted_lambda,
    apply_causal_moving_average,
    calculate_workload_observations,
)


def test_weighted_lambda_calculation():
    """Verify weighted sum formula lambda = sum_k [w_k * count_k]."""
    event_counts = {
        'watch_video': 2,        # 2 * 0.50 = 1.00
        'read_pdf': 3,           # 3 * 0.80 = 2.40
        'attempt_quiz': 1,       # 1 * 2.00 = 2.00
        'prepare_project': 1,    # 1 * 4.00 = 4.00
    }
    expected_sum = 1.00 + 2.40 + 2.00 + 4.00  # 9.40
    raw_lambda = calculate_daily_weighted_lambda(event_counts)
    assert raw_lambda == pytest.approx(expected_sum)

    # Custom weights
    custom_weights = {'custom_task': 2.5}
    assert calculate_daily_weighted_lambda({'custom_task': 4}, weights=custom_weights) == pytest.approx(10.0)


def test_causal_moving_average_uses_no_future_data():
    """Verify causal moving average: t=0 uses only day 0, t=1 uses days 0 and 1 only."""
    series = [10.0, 20.0, 30.0, 100.0]
    smoothed = apply_causal_moving_average(series, window=3)

    # t = 0: mean([10.0]) = 10.0
    assert smoothed[0] == pytest.approx(10.0)

    # t = 1: mean([10.0, 20.0]) = 15.0  (must NOT incorporate 30.0 or 100.0)
    assert smoothed[1] == pytest.approx(15.0)


def test_moving_average_window_3():
    """Verify 3-day backward window formula."""
    series = [3.0, 6.0, 9.0, 12.0, 15.0]
    smoothed = apply_causal_moving_average(series, window=3)

    # t = 0: [3.0] -> 3.0
    assert smoothed[0] == pytest.approx(3.0)
    # t = 1: [3.0, 6.0] -> 4.5
    assert smoothed[1] == pytest.approx(4.5)
    # t = 2: [3.0, 6.0, 9.0] -> 6.0
    assert smoothed[2] == pytest.approx(6.0)
    # t = 3: [6.0, 9.0, 12.0] -> 9.0
    assert smoothed[3] == pytest.approx(9.0)
    # t = 4: [9.0, 12.0, 15.0] -> 12.0
    assert smoothed[4] == pytest.approx(12.0)


def test_workload_categories_separate():
    """Incoming, active, completed, overdue, and ineffective categories must be distinctly kept."""
    student_id = "student-categories"
    d1 = date(2026, 11, 17)
    d2 = date(2026, 11, 18)

    summaries = [
        DailyActivitySummary(
            student_id=student_id,
            date=d1,
            event_counts={'read_pdf': 2, 'login': 1, 'logout': 1},
        ),
        DailyActivitySummary(
            student_id=student_id,
            date=d2,
            event_counts={'attempt_quiz': 1},
        ),
    ]

    task_workloads = {
        d1.isoformat(): {
            'incoming': 5.0,
            'active': 2.0,
            'completed': 1.0,
            'overdue': 0.5,
        },
        d2.isoformat(): {
            'incoming': 3.0,
            'active': 4.0,
            'completed': 3.0,
            'overdue': 0.0,
        },
    }

    observations = calculate_workload_observations(
        student_id=student_id,
        daily_summaries=summaries,
        task_workloads=task_workloads,
    )

    assert len(observations) == 2

    obs1 = observations[0]
    assert obs1.date == d1
    assert obs1.incoming_workload == 5.0
    assert obs1.active_workload == 2.0
    assert obs1.completed_workload == 1.0
    assert obs1.overdue_workload == 0.5
    # login (0.05 < 0.1) and logout (0.00 < 0.1) -> 2 events * 0.05 = 0.10
    assert obs1.ineffective_interactions == pytest.approx(0.10)

    obs2 = observations[1]
    assert obs2.date == d2
    assert obs2.incoming_workload == 3.0
    assert obs2.active_workload == 4.0
    assert obs2.completed_workload == 3.0
    assert obs2.overdue_workload == 0.0
    assert obs2.ineffective_interactions == pytest.approx(0.0)


def test_unknown_event_type_weight_zero():
    """Unknown or unconfigured event types must contribute 0.0 to raw lambda."""
    counts = {
        'completely_unknown_event': 50,
        'unrecognized_telemetry': 100,
    }
    raw_lambda = calculate_daily_weighted_lambda(counts)
    assert raw_lambda == 0.0

    # With a known event mixed in
    counts_mixed = {
        'read_pdf': 1,  # 0.80
        'random_event': 25,
    }
    assert calculate_daily_weighted_lambda(counts_mixed) == pytest.approx(0.80)


def test_chronological_sorting_defensive():
    """calculate_workload_observations must sort out-of-order summaries chronologically."""
    student_id = "student-order"
    d1 = date(2026, 11, 1)
    d2 = date(2026, 11, 2)
    d3 = date(2026, 11, 3)

    # Pass in reverse order
    summaries = [
        DailyActivitySummary(student_id=student_id, date=d3, event_counts={'read_pdf': 3}),
        DailyActivitySummary(student_id=student_id, date=d1, event_counts={'read_pdf': 1}),
        DailyActivitySummary(student_id=student_id, date=d2, event_counts={'read_pdf': 2}),
    ]

    obs = calculate_workload_observations(student_id, summaries)
    assert [o.date for o in obs] == [d1, d2, d3]
    # Check smoothed lambdas match sorted order
    # raw: [0.8, 1.6, 2.4]
    # smoothed: [0.8, 1.2, 1.6]
    assert obs[0].smoothed_lambda == pytest.approx(0.8)
    assert obs[1].smoothed_lambda == pytest.approx(1.2)
    assert obs[2].smoothed_lambda == pytest.approx(1.6)

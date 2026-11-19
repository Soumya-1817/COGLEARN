"""
Calculation Audit Log
=====================
Every cognitive analytics calculation must be traceable to:
  - The student it concerns
  - The input observations used
  - The model version and parameters active at calculation time
  - The output produced
  - The timestamp of calculation

This module provides helpers to format audit entries for each model.
"""

from datetime import datetime
from typing import Any
import json


def make_model1_audit(
    student_id: str,
    model_version_id: str,
    alpha_prior: float,
    beta_prior: float,
    daily_counts_used: list[float],
    n_anomalous_excluded: int,
    alpha_post: float,
    beta_post: float,
    mean_capacity: float,
    ci_lower: float,
    ci_upper: float,
    duration_ms: float,
) -> dict:
    return {
        'student_id': student_id,
        'model_number': 1,
        'model_version_id': model_version_id,
        'input_data': {
            'alpha_prior': alpha_prior,
            'beta_prior': beta_prior,
            'daily_counts': daily_counts_used,
            'n_observations': len(daily_counts_used),
            'n_anomalous_excluded': n_anomalous_excluded,
        },
        'output_data': {
            'alpha_post': alpha_post,
            'beta_post': beta_post,
            'mean_capacity': mean_capacity,
            'ci_lower_95': ci_lower,
            'ci_upper_95': ci_upper,
        },
        'calculation_duration_ms': duration_ms,
        'calculated_at': datetime.utcnow().isoformat(),
        'triggered_by': 'scheduled',
    }


def make_model2_audit(
    student_id: str,
    model_version_id: str,
    lambda_demand: float,
    mu_capacity: float,
    rho: float,
    L: float | None,
    W: float | None,
    is_stable: bool,
    duration_ms: float,
) -> dict:
    return {
        'student_id': student_id,
        'model_number': 2,
        'model_version_id': model_version_id,
        'input_data': {
            'lambda_demand': lambda_demand,
            'mu_capacity': mu_capacity,
        },
        'output_data': {
            'rho': rho,
            'L': L,
            'W': W,
            'is_stable': is_stable,
        },
        'calculation_duration_ms': duration_ms,
        'calculated_at': datetime.utcnow().isoformat(),
        'triggered_by': 'scheduled',
    }


def make_model3_audit(
    student_id: str,
    model_version_id: str,
    date: str,
    event_counts: dict,
    weight_config_version: str,
    raw_lambda: float,
    smoothed_lambda: float,
    duration_ms: float,
) -> dict:
    return {
        'student_id': student_id,
        'model_number': 3,
        'model_version_id': model_version_id,
        'input_data': {
            'date': date,
            'event_counts': event_counts,
            'weight_config_version': weight_config_version,
        },
        'output_data': {
            'raw_lambda': raw_lambda,
            'smoothed_lambda': smoothed_lambda,
        },
        'calculation_duration_ms': duration_ms,
        'calculated_at': datetime.utcnow().isoformat(),
        'triggered_by': 'scheduled',
    }


def make_model4_audit(
    student_id: str,
    model_version_id: str,
    rho_bin: int,
    rho: float,
    p_underload: float,
    p_flow: float,
    p_overload: float,
    p_fatigue: float,
    iori: float,
    risk_zone: str,
    is_provisional: bool,
    duration_ms: float,
) -> dict:
    return {
        'student_id': student_id,
        'model_number': 4,
        'model_version_id': model_version_id,
        'input_data': {
            'rho': rho,
            'rho_bin': rho_bin,
        },
        'output_data': {
            'p_underload': p_underload,
            'p_flow': p_flow,
            'p_overload': p_overload,
            'p_fatigue': p_fatigue,
            'iori': iori,
            'risk_zone': risk_zone,
            'is_provisional_params': is_provisional,
        },
        'calculation_duration_ms': duration_ms,
        'calculated_at': datetime.utcnow().isoformat(),
        'triggered_by': 'scheduled',
    }

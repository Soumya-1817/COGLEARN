"""
Cognitive Analytics Pipeline
=============================
Orchestrates the four-model processing dependency chain:

  Student Activity Events
       |
       v
  [Model 1] Bayesian Capacity Estimation  -->  mu (capacity)
       |
       v
  [Model 3] ICAP Workload Quantification  -->  lambda_bar (smoothed demand)
       |
       v
  [Model 2] M/M/1 Queue Assessment       -->  rho, L, W, stability
       |
       v
  [Model 4] HMM Forward Filter           -->  P(state | observations)
       |
       v
  IORI = P(Overload) + P(Fatigue)
       |
       v
  Intervention Engine (mentor notification if IORI >= threshold)

Every step writes to the calculation_audit_log for full traceability.
The LMS continues to operate even if the analytics pipeline fails.
"""

from datetime import date, datetime
from typing import Optional
import logging

from app.analytics.model1_capacity import estimate_capacity, CapacityPrior
from app.analytics.model2_queue import calculate_queue_metrics
from app.analytics.model3_workload import (
    WorkloadObservation,
    calculate_workload_observations,
    DailyActivitySummary,
)
from app.analytics.model4_hmm import (
    RealTimeHMMFilter,
    HMMParameters,
    ObservationVector,
    discretise_rho,
    HMMStateEstimate,
    RiskZone,
)

logger = logging.getLogger(__name__)


def run_full_pipeline_for_student(
    student_id: str,
    daily_summaries: list[DailyActivitySummary],
    task_workloads: Optional[dict] = None,
    capacity_prior: Optional[CapacityPrior] = None,
    hmm_params: Optional[HMMParameters] = None,
    model_versions: Optional[dict] = None,
) -> dict:
    """
    Execute the complete four-model analytics pipeline for one student.

    Returns a dict with all intermediate and final outputs for audit storage.
    If any model fails, logs the error and returns partial results rather
    than halting the LMS.

    Parameters
    ----------
    student_id      : student UUID string
    daily_summaries : chronological list of daily activity summaries
    task_workloads  : optional task-based workload contributions per date
    capacity_prior  : Bayesian prior for Model 1 (defaults to PROVISIONAL)
    hmm_params      : HMM parameters for Model 4 (defaults to PROVISIONAL)
    model_versions  : version strings for audit traceability

    Returns
    -------
    dict with keys: capacity_estimate, workload_observations, queue_metrics,
                    hmm_estimates, errors
    """
    versions = model_versions or {
        'model1': 'v1.0-provisional',
        'model2': 'v1.0',
        'model3': 'v1.0-provisional',
        'model4': 'v1.0-provisional',
    }

    result = {
        'student_id': student_id,
        'run_at': datetime.utcnow().isoformat(),
        'capacity_estimate': None,
        'workload_observations': [],
        'queue_metrics': [],
        'hmm_estimates': [],
        'errors': [],
    }

    # -------------------------------------------------------------------
    # Model 1: Bayesian Capacity Estimation
    # -------------------------------------------------------------------
    try:
        daily_counts = [sum(s.event_counts.values()) for s in daily_summaries]
        capacity_estimate = estimate_capacity(
            student_id=student_id,
            daily_counts=daily_counts,
            prior=capacity_prior,
            model_version=versions['model1'],
        )
        result['capacity_estimate'] = capacity_estimate
        mu = capacity_estimate.mean_capacity
        logger.info(
            'Model 1 complete for %s: mu=%.4f (CI: %.4f-%.4f)',
            student_id, mu, capacity_estimate.ci_lower_95, capacity_estimate.ci_upper_95
        )
    except Exception as exc:
        logger.error('Model 1 failed for %s: %s', student_id, exc)
        result['errors'].append({'model': 1, 'error': str(exc)})
        mu = None

    # -------------------------------------------------------------------
    # Model 3: ICAP Workload Quantification
    # -------------------------------------------------------------------
    try:
        workload_obs = calculate_workload_observations(
            student_id=student_id,
            daily_summaries=daily_summaries,
            task_workloads=task_workloads,
            model_version=versions['model3'],
        )
        result['workload_observations'] = workload_obs
        logger.info('Model 3 complete for %s: %d observations', student_id, len(workload_obs))
    except Exception as exc:
        logger.error('Model 3 failed for %s: %s', student_id, exc)
        result['errors'].append({'model': 3, 'error': str(exc)})
        workload_obs = []

    # -------------------------------------------------------------------
    # Model 2: M/M/1 Queue Assessment
    # -------------------------------------------------------------------
    if mu is not None and workload_obs:
        try:
            queue_metrics_list = []
            for obs in workload_obs:
                qm = calculate_queue_metrics(
                    student_id=student_id,
                    lambda_demand=obs.smoothed_lambda,
                    mu_capacity=mu,
                    observation_date=obs.date,
                    model_version=versions['model2'],
                )
                queue_metrics_list.append(qm)
            result['queue_metrics'] = queue_metrics_list
            latest_rho = queue_metrics_list[-1].rho if queue_metrics_list else 0.0
            logger.info('Model 2 complete for %s: latest rho=%.4f', student_id, latest_rho)
        except Exception as exc:
            logger.error('Model 2 failed for %s: %s', student_id, exc)
            result['errors'].append({'model': 2, 'error': str(exc)})
            queue_metrics_list = []
    else:
        queue_metrics_list = []

    # -------------------------------------------------------------------
    # Model 4: HMM Forward Filter + IORI
    # -------------------------------------------------------------------
    if queue_metrics_list:
        try:
            hmm_filter = RealTimeHMMFilter(
                student_id=student_id,
                params=hmm_params,
            )
            hmm_estimates = []
            for qm in queue_metrics_list:
                rho = qm.rho if qm.is_stable else 1.5  # Map unstable to overload bin
                obs_bin = discretise_rho(rho)
                obs = ObservationVector(
                    rho=rho,
                    rho_bin=obs_bin,
                    raw_features={
                        'is_stable': qm.is_stable,
                        'lambda_demand': qm.lambda_demand,
                        'mu_capacity': qm.mu_capacity,
                        'date': qm.date.isoformat(),
                    },
                )
                estimate = hmm_filter.current_estimate(
                    obs,
                    timestamp=datetime.combine(qm.date, datetime.min.time()),
                )
                hmm_estimates.append(estimate)
            result['hmm_estimates'] = hmm_estimates

            if hmm_estimates:
                latest = hmm_estimates[-1]
                logger.info(
                    'Model 4 + IORI for %s: state=%s IORI=%.4f zone=%s',
                    student_id, latest.dominant_state, latest.iori, latest.risk_zone
                )
        except Exception as exc:
            logger.error('Model 4 failed for %s: %s', student_id, exc)
            result['errors'].append({'model': 4, 'error': str(exc)})

    return result

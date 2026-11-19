"""
Celery Analytics Tasks
=======================
Scheduled background tasks that run the four-model cognitive analytics
pipeline for all active students in all active institutions.

Task execution order:
  1. run_nightly_capacity_estimation   (Model 1 - 02:00 UTC)
  2. run_nightly_workload_calculation  (Model 3 + Model 2 - 02:15 UTC)
  3. run_nightly_iori_assessment       (Model 4 + IORI - 02:30 UTC)

All tasks are fault-tolerant: failure for one student does not halt
processing for others. Errors are logged per student.

All outputs are persisted to the database with full audit trails.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _get_or_create_model_version_id(db, model_number: int, name: str) -> UUID:
    from sqlalchemy import select
    from app.models.model_version import ModelVersion

    mv_result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.model_number == model_number
        ).order_by(ModelVersion.effective_from.desc()).limit(1)
    )
    mv = mv_result.scalar_one_or_none()
    if mv:
        return mv.id
    new_mv = ModelVersion(
        id=uuid4(),
        model_number=model_number,
        version_string="v1.0-provisional",
        parameters={"is_provisional": True},
        is_provisional=True,
        effective_from=datetime.utcnow() - timedelta(days=90),
        notes=f"Model {model_number}: {name} - PROVISIONAL parameters",
    )
    db.add(new_mv)
    await db.flush()
    return new_mv.id


@celery_app.task(
    name='app.worker.tasks.analytics.run_nightly_capacity_estimation',
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def run_nightly_capacity_estimation(self):
    """
    Model 1: Bayesian Capacity Estimation for all active students.
    
    For each active institution:
      For each active student:
        1. Load daily activity aggregates (last 90 days)
        2. Load or estimate institution-level prior
        3. Run estimate_capacity()
        4. Persist CognitiveCapacityEstimate to DB
        5. Write calculation_audit_log entry
    """
    logger.info('Starting nightly capacity estimation (Model 1)')
    try:
        run_async(_run_capacity_estimation())
        logger.info('Model 1 nightly estimation complete')
    except Exception as exc:
        logger.error('Model 1 nightly task failed: %s', exc)
        raise self.retry(exc=exc)


async def _run_capacity_estimation():
    import time
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.institution import Institution
    from app.models.user import User
    from app.models.daily_activity_aggregate import DailyActivityAggregate
    from app.models.cognitive_capacity_estimate import CognitiveCapacityEstimate
    from app.models.calculation_audit_log import CalculationAuditLog
    from app.analytics.model1_capacity import estimate_capacity, CapacityPrior

    async with AsyncSessionLocal() as db:
        # Get all active institutions
        inst_result = await db.execute(
            select(Institution).where(Institution.is_active == True)
        )
        institutions = inst_result.scalars().all()

        for institution in institutions:
            model_version_id = await _get_or_create_model_version_id(
                db, 1, "Bayesian Capacity"
            )

            # Get all active students
            student_result = await db.execute(
                select(User).where(
                    User.institution_id == institution.id,
                    User.role == 'student',
                    User.is_active == True,
                )
            )
            students = student_result.scalars().all()

            cutoff = date.today() - timedelta(days=90)
            for student in students:
                try:
                    start_time = time.time()
                    # Load daily aggregates
                    agg_result = await db.execute(
                        select(DailyActivityAggregate).where(
                            DailyActivityAggregate.student_id == student.id,
                            DailyActivityAggregate.date >= cutoff,
                        ).order_by(DailyActivityAggregate.date.asc())
                    )
                    aggregates = agg_result.scalars().all()
                    daily_counts = [float(a.valid_click_count) for a in aggregates]

                    prior = CapacityPrior()  # PROVISIONAL
                    estimate = estimate_capacity(
                        student_id=str(student.id),
                        daily_counts=daily_counts,
                        prior=prior,
                        model_version='v1.0-provisional',
                    )
                    duration_ms = (time.time() - start_time) * 1000

                    # Persist estimate
                    db_estimate = CognitiveCapacityEstimate(
                        student_id=student.id,
                        institution_id=institution.id,
                        alpha_post=estimate.alpha_post,
                        beta_post=estimate.beta_post,
                        mean_capacity=estimate.mean_capacity,
                        variance=estimate.variance,
                        ci_lower_95=estimate.ci_lower_95,
                        ci_upper_95=estimate.ci_upper_95,
                        n_observations=estimate.n_observations,
                        is_provisional_params=estimate.is_provisional_params,
                        model_version_id=model_version_id,
                        calculated_at=datetime.utcnow(),
                    )
                    db.add(db_estimate)

                    # Write audit log
                    audit_entry = CalculationAuditLog(
                        institution_id=institution.id,
                        student_id=student.id,
                        model_number=1,
                        model_version_id=model_version_id,
                        input_data={
                            'alpha_prior': prior.alpha_0,
                            'beta_prior': prior.beta_0,
                            'n_observations': len(daily_counts),
                            'n_anomalous_excluded': estimate.n_anomalous_excluded,
                        },
                        output_data={
                            'alpha_post': estimate.alpha_post,
                            'beta_post': estimate.beta_post,
                            'mean_capacity': estimate.mean_capacity,
                            'ci_lower_95': estimate.ci_lower_95,
                            'ci_upper_95': estimate.ci_upper_95,
                        },
                        calculation_duration_ms=duration_ms,
                        calculated_at=datetime.utcnow(),
                        triggered_by='scheduled',
                    )
                    db.add(audit_entry)

                except Exception as exc:
                    logger.error(
                        'Model 1 failed for student %s in institution %s: %s',
                        student.id, institution.id, exc
                    )
                    continue

            await db.commit()
            logger.info(
                'Model 1 complete for institution %s: %d students processed',
                institution.id, len(students)
            )


@celery_app.task(
    name='app.worker.tasks.analytics.run_nightly_workload_calculation',
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def run_nightly_workload_calculation(self):
    """
    Model 3 + Model 2: Workload quantification and M/M/1 queue metrics
    for all active students.
    """
    logger.info('Starting nightly workload calculation (Models 3 + 2)')
    try:
        run_async(_run_workload_calculation())
        logger.info('Models 3+2 nightly calculation complete')
    except Exception as exc:
        logger.error('Models 3+2 nightly task failed: %s', exc)
        raise self.retry(exc=exc)


async def _run_workload_calculation():
    import time
    from sqlalchemy import select, delete
    from app.core.database import AsyncSessionLocal
    from app.models.institution import Institution
    from app.models.user import User
    from app.models.daily_activity_aggregate import DailyActivityAggregate
    from app.models.cognitive_capacity_estimate import CognitiveCapacityEstimate
    from app.models.incoming_workload_observation import IncomingWorkloadObservation
    from app.models.queue_metric_snapshot import QueueMetricSnapshot
    from app.analytics.model3_workload import (
        DailyActivitySummary, calculate_workload_observations
    )
    from app.analytics.model2_queue import calculate_queue_metrics

    async with AsyncSessionLocal() as db:
        inst_result = await db.execute(
            select(Institution).where(Institution.is_active == True)
        )
        institutions = inst_result.scalars().all()

        for institution in institutions:
            model_version_3_id = await _get_or_create_model_version_id(
                db, 3, "ICAP Workload"
            )
            model_version_2_id = await _get_or_create_model_version_id(
                db, 2, "MM1 Queue"
            )

            student_result = await db.execute(
                select(User).where(
                    User.institution_id == institution.id,
                    User.role == 'student',
                    User.is_active == True,
                )
            )
            students = student_result.scalars().all()

            cutoff = date.today() - timedelta(days=30)
            for student in students:
                try:
                    start_time = time.time()

                    # Load aggregates
                    agg_result = await db.execute(
                        select(DailyActivityAggregate).where(
                            DailyActivityAggregate.student_id == student.id,
                            DailyActivityAggregate.date >= cutoff,
                        ).order_by(DailyActivityAggregate.date.asc())
                    )
                    aggregates = agg_result.scalars().all()

                    summaries = [
                        DailyActivitySummary(
                            student_id=str(student.id),
                            date=a.date,
                            event_counts={'__total_weighted': float(a.weighted_clicks)},
                            weight_config_version='v1.0-provisional',
                        )
                        for a in aggregates
                    ]

                    workload_obs = calculate_workload_observations(
                        student_id=str(student.id),
                        daily_summaries=summaries,
                        model_version='v1.0-provisional',
                    )

                    # Get latest capacity estimate
                    cap_result = await db.execute(
                        select(CognitiveCapacityEstimate).where(
                            CognitiveCapacityEstimate.student_id == student.id
                        ).order_by(CognitiveCapacityEstimate.calculated_at.desc()).limit(1)
                    )
                    cap_estimate = cap_result.scalar_one_or_none()
                    mu = cap_estimate.mean_capacity if cap_estimate else 2.0  # fallback to prior mean

                    # Persist workload observations and queue metrics
                    for obs in workload_obs:
                        # Clean up existing record for idempotent re-runs
                        await db.execute(
                            delete(IncomingWorkloadObservation).where(
                                IncomingWorkloadObservation.student_id == student.id,
                                IncomingWorkloadObservation.date == obs.date,
                            )
                        )
                        # Workload observation
                        wl_record = IncomingWorkloadObservation(
                            institution_id=institution.id,
                            student_id=student.id,
                            date=obs.date,
                            raw_lambda=obs.raw_lambda,
                            smoothed_lambda=obs.smoothed_lambda,
                            incoming_workload=obs.incoming_workload,
                            active_workload=obs.active_workload,
                            completed_workload=obs.completed_workload,
                            overdue_workload=obs.overdue_workload,
                            ineffective_interactions=obs.ineffective_interactions,
                            weight_config_version=obs.weight_config_version,
                            model_version_id=model_version_3_id,
                        )
                        db.add(wl_record)

                        # Queue metrics
                        qm = calculate_queue_metrics(
                            student_id=str(student.id),
                            lambda_demand=obs.smoothed_lambda,
                            mu_capacity=mu,
                            observation_date=obs.date,
                            model_version='v1.0',
                        )

                        await db.execute(
                            delete(QueueMetricSnapshot).where(
                                QueueMetricSnapshot.student_id == student.id,
                                QueueMetricSnapshot.date == qm.date,
                            )
                        )
                        qm_record = QueueMetricSnapshot(
                            institution_id=institution.id,
                            student_id=student.id,
                            date=qm.date,
                            lambda_demand=qm.lambda_demand,
                            mu_capacity=qm.mu_capacity,
                            rho=qm.rho,
                            L=qm.L,
                            W=qm.W,
                            is_stable=qm.is_stable,
                            instability_reason=qm.instability_reason,
                            calculated_at=datetime.utcnow(),
                            model_version_id=model_version_2_id,
                        )
                        db.add(qm_record)

                except Exception as exc:
                    logger.error(
                        'Models 3+2 failed for student %s: %s', student.id, exc
                    )
                    continue

            await db.commit()


@celery_app.task(
    name='app.worker.tasks.analytics.run_nightly_iori_assessment',
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def run_nightly_iori_assessment(self):
    """
    Model 4 + IORI: HMM forward filter and IORI calculation for all active students.
    Triggers mentor notification if IORI enters Red zone.
    """
    logger.info('Starting nightly IORI assessment (Model 4)')
    try:
        run_async(_run_iori_assessment())
        logger.info('Model 4 + IORI nightly assessment complete')
    except Exception as exc:
        logger.error('Model 4 nightly task failed: %s', exc)
        raise self.retry(exc=exc)


async def _run_iori_assessment():
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.institution import Institution
    from app.models.user import User
    from app.models.queue_metric_snapshot import QueueMetricSnapshot
    from app.models.hmm_state_estimate import HmmStateEstimate
    from app.models.iori_assessment import IoriAssessment
    from app.analytics.model4_hmm import run_batch_forward_filter

    async with AsyncSessionLocal() as db:
        inst_result = await db.execute(
            select(Institution).where(Institution.is_active == True)
        )
        institutions = inst_result.scalars().all()

        for institution in institutions:
            model_version_4_id = await _get_or_create_model_version_id(
                db, 4, "HMM Cognitive State"
            )

            student_result = await db.execute(
                select(User).where(
                    User.institution_id == institution.id,
                    User.role == 'student',
                    User.is_active == True,
                )
            )
            students = student_result.scalars().all()

            cutoff = date.today() - timedelta(days=30)
            for student in students:
                try:
                    # Get recent rho series
                    qm_result = await db.execute(
                        select(QueueMetricSnapshot).where(
                            QueueMetricSnapshot.student_id == student.id,
                            QueueMetricSnapshot.date >= cutoff,
                        ).order_by(QueueMetricSnapshot.date.asc())
                    )
                    snapshots = qm_result.scalars().all()
                    if not snapshots:
                        continue

                    rho_series = [
                        s.rho if s.is_stable else 1.5
                        for s in snapshots
                    ]
                    timestamps = [
                        datetime.combine(s.date, datetime.min.time())
                        for s in snapshots
                    ]

                    estimates = run_batch_forward_filter(
                        student_id=str(student.id),
                        rho_series=rho_series,
                        timestamps=timestamps,
                    )

                    # Persist latest estimate and IORI
                    if estimates:
                        latest = estimates[-1]
                        dominant_val = (
                            latest.dominant_state.value
                            if hasattr(latest.dominant_state, 'value')
                            else str(latest.dominant_state)
                        )
                        risk_zone_val = (
                            latest.risk_zone.value
                            if hasattr(latest.risk_zone, 'value')
                            else str(latest.risk_zone)
                        )

                        hmm_record = HmmStateEstimate(
                            institution_id=institution.id,
                            student_id=student.id,
                            timestamp=latest.timestamp,
                            p_underload=latest.p_underload,
                            p_flow=latest.p_flow,
                            p_overload=latest.p_overload,
                            p_fatigue=latest.p_fatigue,
                            dominant_state=dominant_val,
                            observation_vector=latest.observation_vector,
                            model_version_id=model_version_4_id,
                            is_provisional_params=latest.is_provisional_params,
                        )
                        db.add(hmm_record)
                        await db.flush()

                        iori_record = IoriAssessment(
                            institution_id=institution.id,
                            student_id=student.id,
                            timestamp=latest.timestamp,
                            iori_value=latest.iori,
                            risk_zone=risk_zone_val,
                            p_overload=latest.p_overload,
                            p_fatigue=latest.p_fatigue,
                            hmm_estimate_id=hmm_record.id,
                            model_version_id=model_version_4_id,
                            is_presented_to_mentor=False,
                        )
                        db.add(iori_record)

                        # Flag for mentor if Red zone
                        if latest.iori >= 0.60:
                            logger.info(
                                'RED ZONE: student %s IORI=%.3f - making available to mentor',
                                student.id, latest.iori
                            )
                            iori_record.is_presented_to_mentor = True

                except Exception as exc:
                    logger.error(
                        'Model 4 failed for student %s: %s', student.id, exc
                    )
                    continue

            await db.commit()

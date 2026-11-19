"""
Mentor Intervention Engine
==========================
Provides tools for mentors to support at-risk students.

Trigger conditions:
  - IORI >= 0.60 (Red zone) makes student analytics available to mentor
  - Mentor manually opens an intervention
  - Student submits a mentorship request

IMPORTANT:
  - IORI is a support indicator, NOT a medical diagnosis
  - Mental-health referrals require explicit consent and institutional procedure
  - Mentor can view analytics but cannot take automatic action on the student
  - Intervention records and messages are PRIVATE
  - Student can request help independently of IORI
"""

from datetime import datetime, timezone
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intervention import Intervention, InterventionStatus, InterventionTriggerType
from app.models.iori_assessment import IORIAssessment
from app.models.mental_health_referral import MentalHealthReferral, ReferralStatus
from app.models.mentor_message import MentorMessage
from app.models.mentorship_request import MentorshipRequest, MentorshipRequestStatus
from app.models.queue_metric_snapshot import QueueMetricSnapshot
from app.models.user import User

logger = logging.getLogger(__name__)


def _model_to_dict(model_instance: Any) -> dict[str, Any]:
    """Serializes a SQLAlchemy model instance into a dictionary."""
    if model_instance is None:
        return {}
    res = {}
    for column in model_instance.__table__.columns:
        val = getattr(model_instance, column.name)
        if isinstance(val, UUID):
            res[column.name] = str(val)
        elif isinstance(val, datetime):
            res[column.name] = val.isoformat()
        elif hasattr(val, "value"):
            res[column.name] = val.value
        else:
            res[column.name] = val
    return res


async def create_intervention(
    db: AsyncSession,
    institution_id: UUID,
    mentor_id: UUID,
    student_id: UUID,
    trigger_type: str,
    iori_value: Optional[float] = None,
    risk_zone: Optional[str] = None,
) -> dict:
    """
    Creates an academic intervention record initiated by IORI trigger,
    manual mentor outreach, or student request.
    """
    try:
        trig_enum = InterventionTriggerType(trigger_type.lower())
    except ValueError:
        trig_enum = InterventionTriggerType.MANUAL

    intervention = Intervention(
        id=uuid4(),
        institution_id=institution_id,
        mentor_id=mentor_id,
        student_id=student_id,
        trigger_type=trig_enum,
        iori_value_at_trigger=iori_value,
        risk_zone_at_trigger=risk_zone,
        status=InterventionStatus.OPEN,
    )
    db.add(intervention)
    await db.commit()
    await db.refresh(intervention)
    return _model_to_dict(intervention)


async def get_mentor_interventions(
    db: AsyncSession,
    institution_id: UUID,
    mentor_id: UUID,
    status: Optional[str] = None,
) -> list[dict]:
    """Retrieves all interventions assigned to or managed by a mentor."""
    conditions = [
        Intervention.mentor_id == mentor_id,
        Intervention.institution_id == institution_id,
    ]
    if status:
        try:
            status_enum = InterventionStatus(status.lower())
            conditions.append(Intervention.status == status_enum)
        except ValueError:
            pass

    stmt = select(Intervention).where(and_(*conditions)).order_by(Intervention.created_at.desc())
    result = await db.execute(stmt)
    interventions = result.scalars().all()
    return [_model_to_dict(i) for i in interventions]


async def send_mentor_message(
    db: AsyncSession,
    institution_id: UUID,
    intervention_id: UUID,
    sender_id: UUID,
    recipient_id: UUID,
    body: str,
) -> dict:
    """Sends a private message between mentor and student within an intervention."""
    # Verify intervention
    int_stmt = select(Intervention).where(
        and_(
            Intervention.id == intervention_id,
            Intervention.institution_id == institution_id,
        )
    )
    intervention = (await db.execute(int_stmt)).scalar_one_or_none()
    if intervention is None:
        raise ValueError(f"Intervention {intervention_id} not found.")

    # Validate sender/recipient are participants
    participants = {intervention.mentor_id, intervention.student_id}
    if sender_id not in participants or recipient_id not in participants:
        raise ValueError("Sender or recipient is not a participant in this intervention.")

    msg = MentorMessage(
        id=uuid4(),
        institution_id=institution_id,
        intervention_id=intervention_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        body=body.strip(),
        is_read=False,
    )
    db.add(msg)

    # If intervention was OPEN, advance to IN_PROGRESS
    if intervention.status == InterventionStatus.OPEN:
        intervention.status = InterventionStatus.IN_PROGRESS
        intervention.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(msg)
    return _model_to_dict(msg)


async def get_intervention_messages(
    db: AsyncSession,
    institution_id: UUID,
    intervention_id: UUID,
    requesting_user_id: UUID,
) -> list[dict]:
    """
    Returns messages only if requesting_user_id is a participant.
    """
    int_stmt = select(Intervention).where(
        and_(
            Intervention.id == intervention_id,
            Intervention.institution_id == institution_id,
        )
    )
    intervention = (await db.execute(int_stmt)).scalar_one_or_none()
    if intervention is None:
        raise ValueError(f"Intervention {intervention_id} not found.")

    if requesting_user_id not in {intervention.mentor_id, intervention.student_id}:
        raise PermissionError("Access denied: You are not a participant in this intervention.")

    stmt = (
        select(MentorMessage)
        .where(
            and_(
                MentorMessage.intervention_id == intervention_id,
                MentorMessage.institution_id == institution_id,
            )
        )
        .order_by(MentorMessage.sent_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return [_model_to_dict(m) for m in messages]


async def create_mentorship_request(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
    message: str,
) -> dict:
    """
    Student-initiated request for mentorship.
    Independent of IORI - any student can request help at any time.
    """
    req = MentorshipRequest(
        id=uuid4(),
        institution_id=institution_id,
        student_id=student_id,
        message=message.strip(),
        status=MentorshipRequestStatus.PENDING,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return _model_to_dict(req)


async def accept_mentorship_request(
    db: AsyncSession,
    institution_id: UUID,
    request_id: UUID,
    mentor_id: UUID,
) -> dict:
    """
    Mentor accepts a student mentorship request and opens an intervention.
    """
    stmt = select(MentorshipRequest).where(
        and_(
            MentorshipRequest.id == request_id,
            MentorshipRequest.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise ValueError(f"Mentorship request {request_id} not found.")

    req.mentor_id = mentor_id
    req.status = MentorshipRequestStatus.ACCEPTED
    req.updated_at = datetime.now(timezone.utc)

    # Automatically create intervention
    intervention = Intervention(
        id=uuid4(),
        institution_id=institution_id,
        mentor_id=mentor_id,
        student_id=req.student_id,
        trigger_type=InterventionTriggerType.STUDENT_REQUEST,
        status=InterventionStatus.OPEN,
    )
    db.add(intervention)

    await db.commit()
    await db.refresh(req)
    await db.refresh(intervention)

    out = _model_to_dict(req)
    out["intervention_id"] = str(intervention.id)
    return out


async def close_intervention(
    db: AsyncSession,
    institution_id: UUID,
    intervention_id: UUID,
    mentor_id: UUID,
    summary_notes: str,
) -> dict:
    """Closes an active intervention with mentor summary notes."""
    stmt = select(Intervention).where(
        and_(
            Intervention.id == intervention_id,
            Intervention.institution_id == institution_id,
            Intervention.mentor_id == mentor_id,
        )
    )
    result = await db.execute(stmt)
    intervention = result.scalar_one_or_none()
    if intervention is None:
        raise ValueError(f"Intervention {intervention_id} not found or unauthorized.")

    intervention.status = InterventionStatus.CLOSED
    intervention.summary_notes = summary_notes.strip()
    intervention.closed_at = datetime.now(timezone.utc)
    intervention.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(intervention)
    return _model_to_dict(intervention)


async def create_mental_health_referral(
    db: AsyncSession,
    institution_id: UUID,
    mentor_id: UUID,
    student_id: UUID,
    referral_body: str,
    consent_recorded: bool,
) -> dict:
    """
    Create a mental health referral record.
    RESTRICTED: requires referral:read permission to access.
    Consent must be explicitly recorded.
    referral_body should be encrypted at rest in production.
    This is NOT an automatic action - requires mentor judgment and
    institutional authorization procedure.
    """
    if not consent_recorded:
        raise ValueError("Explicit student consent must be recorded prior to mental health referral creation.")

    now = datetime.now(timezone.utc)
    referral = MentalHealthReferral(
        id=uuid4(),
        institution_id=institution_id,
        student_id=student_id,
        referred_by_mentor_id=mentor_id,
        referral_body=referral_body.strip(),
        consent_recorded_at=now if consent_recorded else None,
        status=ReferralStatus.PENDING,
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return _model_to_dict(referral)


async def get_mentor_student_analytics(
    db: AsyncSession,
    institution_id: UUID,
    mentor_id: UUID,
    student_id: UUID,
) -> dict:
    """
    Returns authorized analytics for a student, visible to their mentor.
    Includes: workload summary, IORI history, queue metrics, task list.
    Does NOT include: raw HMM probabilities, referral records,
    medical information, or other students' data.
    """
    # 1. Workload Summary
    from app.services.task_queue_service import calculate_student_weighted_workload, get_student_pending_queue
    workload = await calculate_student_weighted_workload(db, institution_id, student_id)

    # 2. IORI History (past 10 evaluations)
    iori_stmt = (
        select(IORIAssessment)
        .where(
            and_(
                IORIAssessment.student_id == student_id,
                IORIAssessment.institution_id == institution_id,
            )
        )
        .order_by(IORIAssessment.timestamp.desc())
        .limit(10)
    )
    iori_res = await db.execute(iori_stmt)
    iori_records = iori_res.scalars().all()
    iori_history = [
        {
            "id": str(r.id),
            "timestamp": r.timestamp.isoformat(),
            "iori_value": r.iori_value,
            "risk_zone": r.risk_zone.value if hasattr(r.risk_zone, "value") else str(r.risk_zone),
        }
        for r in iori_records
    ]

    # 3. Latest M/M/1 Queue Metric Snapshot
    queue_stmt = (
        select(QueueMetricSnapshot)
        .where(
            and_(
                QueueMetricSnapshot.student_id == student_id,
                QueueMetricSnapshot.institution_id == institution_id,
            )
        )
        .order_by(QueueMetricSnapshot.date.desc())
        .limit(1)
    )
    queue_res = await db.execute(queue_stmt)
    queue_rec = queue_res.scalar_one_or_none()
    queue_metrics = (
        {
            "date": queue_rec.date.isoformat(),
            "lambda_demand": queue_rec.lambda_demand,
            "mu_capacity": queue_rec.mu_capacity,
            "rho": queue_rec.rho,
            "L": queue_rec.L,
            "W": queue_rec.W,
            "is_stable": queue_rec.is_stable,
        }
        if queue_rec
        else None
    )

    # 4. Pending Academic Tasks
    tasks = await get_student_pending_queue(db, institution_id, student_id)

    return {
        "student_id": str(student_id),
        "workload_breakdown": workload,
        "iori_history": iori_history,
        "latest_queue_metrics": queue_metrics,
        "pending_tasks": tasks,
    }

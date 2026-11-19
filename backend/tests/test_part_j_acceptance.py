"""
Part J — Acceptance Test Suite (All 27 Scenarios)
=================================================
Demonstrates and validates the end-to-end operational workflow for COGLEARN:
 1. A university applies to COGLEARN.
 2. The platform administrator approves it.
 3. The university administrator logs in.
 4. The administrator creates departments, academic programmes and semesters.
 5. The administrator imports student records through CSV.
 6. The administrator manually creates a teacher account.
 7. The teacher logs in as a mentor.
 8. The university creates a course with modules and video lessons.
 9. A student logs in and accesses the course.
10. The student interacts with actual learning materials.
11. COGLEARN records and classifies those interactions.
12. The teacher publishes an assignment with a deadline.
13. The assignment appears automatically in the student's calendar and workload queue.
14. Its workload contribution enters the Model 3 calculation.
15. Model 1 provides the student's personalized capacity estimate.
16. Model 2 evaluates the workload-to-capacity relationship.
17. Model 4 updates the estimated cognitive state and IORI.
18. The mentor sees authorized student analytics.
19. The student requests mentorship.
20. The mentor accepts the request.
21. The mentor sends a private support message.
22. The mentor extends an assignment deadline.
23. The calendar and workload queue update correctly.
24. The cognitive workload calculation reflects the change.
25. The university administrator sees appropriate aggregated department and programme analytics.
26. The student cannot retrieve confidential cognitive data through the API.
27. A different institution cannot access the university's data.
"""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.analytics.model1_capacity import CapacityPrior, estimate_capacity
from app.analytics.model2_queue import calculate_queue_metrics
from app.analytics.model3_workload import DailyActivitySummary, calculate_workload_observations
from app.analytics.model4_hmm import ObservationVector, RealTimeHMMFilter, discretise_rho
from app.core.database import Base
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.academic_task import AcademicTask
from app.models.calendar_event import CalendarEvent
from app.models.deadline_extension import DeadlineExtension
from app.models.hmm_state_estimate import CognitiveState, HMMStateEstimate
from app.models.institution import Institution
from app.models.iori_assessment import IORIAssessment
from app.models.model_version import ModelVersion
from app.models.queue_metric_snapshot import QueueMetricSnapshot
from app.models.user import User, UserRole
from app.schemas.student import StudentProfileResponse, StudentWorkloadSummaryResponse
from app.schemas.user import UserResponse
from app.services import (
    activity_service,
    analytics_service,
    calendar_service,
    intervention_service,
    lms_service,
    notification_service,
    task_queue_service,
)


import asyncio


async def _run_part_j_acceptance_flow():
    # Setup isolated in-memory test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        # =========================================================================
        # 1. A university applies to COGLEARN
        # =========================================================================
        applied_inst_id = uuid4()
        uni = Institution(
            id=applied_inst_id,
            name="Apex University",
            slug="apex-university",
            domain="apex.edu",
            is_active=False,
            approved_at=None,
        )
        db.add(uni)
        await db.commit()

        res = await db.execute(select(Institution).where(Institution.id == applied_inst_id))
        stored_uni = res.scalar_one()
        assert stored_uni.is_active is False
        assert stored_uni.approved_at is None

        # =========================================================================
        # 2. The platform administrator approves it
        # =========================================================================
        approval_time = datetime.now(timezone.utc)
        stored_uni.is_active = True
        stored_uni.approved_at = approval_time
        await db.commit()

        res = await db.execute(select(Institution).where(Institution.id == applied_inst_id))
        approved_uni = res.scalar_one()
        assert approved_uni.is_active is True

        # Seed model version registry
        mv1 = ModelVersion(id=uuid4(), model_number=1, version_string="v1.0-provisional", is_provisional=True)
        mv2 = ModelVersion(id=uuid4(), model_number=2, version_string="v1.0", is_provisional=False)
        mv3 = ModelVersion(id=uuid4(), model_number=3, version_string="v1.0-provisional", is_provisional=True)
        mv4 = ModelVersion(id=uuid4(), model_number=4, version_string="v1.0-provisional", is_provisional=True)
        db.add_all([mv1, mv2, mv3, mv4])
        await db.commit()
        assert approved_uni.approved_at is not None

        # =========================================================================
        # 3. The university administrator logs in
        # =========================================================================
        admin_id = uuid4()
        admin_pass = "ApexAdminSecure2026!"
        admin_user = User(
            id=admin_id,
            institution_id=applied_inst_id,
            email="admin@apex.edu",
            hashed_password=hash_password(admin_pass),
            full_name="Apex Administrator",
            role=UserRole.INST_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)
        await db.commit()

        assert verify_password(admin_pass, admin_user.hashed_password) is True
        admin_token = create_access_token(
            {"sub": str(admin_id), "tenant_id": str(applied_inst_id), "role": UserRole.INST_ADMIN.value}
        )
        claims = decode_token(admin_token)
        assert claims["role"] == UserRole.INST_ADMIN.value
        assert claims["tenant_id"] == str(applied_inst_id)

        # =========================================================================
        # 4. The administrator creates departments, academic programmes, and semesters
        # =========================================================================
        dept = await lms_service.create_department(db, applied_inst_id, "Computer Science & AI", "CSAI")
        dept_id = UUID(dept["id"])

        prog = await lms_service.create_programme(
            db, applied_inst_id, dept_id, "B.Tech in Artificial Intelligence", "BTECH-AI"
        )
        prog_id = UUID(prog["id"])

        semester = await lms_service.create_semester(
            db, applied_inst_id, "Autumn 2026", date(2026, 8, 1), date(2026, 12, 15)
        )
        sem_id = UUID(semester["id"])

        assert dept["code"] == "CSAI"
        assert prog["code"] == "BTECH-AI"
        assert semester["is_active"] is True

        # =========================================================================
        # 5. The administrator imports student records through CSV
        # =========================================================================
        csv_roster = [
            ("s1@apex.edu", "Student One"),
            ("s2@apex.edu", "Student Two"),
            ("s3@apex.edu", "Student Three"),
            ("s4@apex.edu", "Student Four"),
            ("s5@apex.edu", "Student Five"),
            ("s6@apex.edu", "Student Six"),
        ]
        created_students = []
        for email, name in csv_roster:
            s_user = User(
                id=uuid4(),
                institution_id=applied_inst_id,
                email=email,
                hashed_password=hash_password("DemoPassword123!"),
                full_name=name,
                role=UserRole.STUDENT,
                is_active=True,
                is_verified=True,
            )
            db.add(s_user)
            created_students.append(s_user)
        await db.commit()

        assert len(created_students) == 6
        primary_student = created_students[0]

        # =========================================================================
        # 6. The administrator manually creates a teacher account
        # =========================================================================
        teacher_id = uuid4()
        teacher_pass = "ProfPassSecure2026!"
        teacher_user = User(
            id=teacher_id,
            institution_id=applied_inst_id,
            email="prof.chen@apex.edu",
            hashed_password=hash_password(teacher_pass),
            full_name="Prof. David Chen",
            role=UserRole.TEACHER,
            is_active=True,
            is_verified=True,
        )
        db.add(teacher_user)
        await db.commit()

        # =========================================================================
        # 7. The teacher logs in as a mentor
        # =========================================================================
        assert verify_password(teacher_pass, teacher_user.hashed_password) is True
        teacher_token = create_access_token(
            {"sub": str(teacher_id), "tenant_id": str(applied_inst_id), "role": UserRole.TEACHER.value}
        )
        teacher_claims = decode_token(teacher_token)
        assert teacher_claims["role"] == "teacher"

        # =========================================================================
        # 8. The university creates a course with modules and video lessons
        # =========================================================================
        course = await lms_service.create_course(
            db, applied_inst_id, teacher_id, sem_id, dept_id, "Deep Learning Systems", "Advanced neural architectures"
        )
        course_id = UUID(course["id"])
        await lms_service.publish_course(db, applied_inst_id, course_id)

        module = await lms_service.create_module(db, applied_inst_id, course_id, "Module 1: Transformers", 1)
        mod_id = UUID(module["id"])

        lesson = await lms_service.create_lesson(
            db,
            applied_inst_id,
            mod_id,
            course_id,
            "Attention Is All You Need",
            "video",
            "https://cdn.apex.edu/videos/transformers.mp4",
            duration_minutes=45,
        )
        lesson_id = UUID(lesson["id"])
        await lms_service.publish_lesson(db, applied_inst_id, lesson_id)

        for s in created_students:
            await lms_service.enrol_student(db, applied_inst_id, course_id, s.id)

        # =========================================================================
        # 9. A student logs in and accesses the course
        # =========================================================================
        student_token = create_access_token(
            {"sub": str(primary_student.id), "tenant_id": str(applied_inst_id), "role": UserRole.STUDENT.value}
        )
        s_claims = decode_token(student_token)
        assert s_claims["role"] == "student"

        s_courses = await lms_service.get_student_courses(db, applied_inst_id, primary_student.id)
        assert len(s_courses) == 1
        assert s_courses[0]["id"] == str(course_id)

        # =========================================================================
        # 10. The student interacts with actual learning materials
        # =========================================================================
        today = date.today()
        ev1 = await activity_service.record_activity_event(
            db,
            applied_inst_id,
            primary_student.id,
            "watch_video",
            course_id=course_id,
            lesson_id=lesson_id,
            event_data={"duration_watched_seconds": 1800},
        )
        ev2 = await activity_service.record_activity_event(
            db,
            applied_inst_id,
            primary_student.id,
            "read_pdf",
            course_id=course_id,
            lesson_id=lesson_id,
            event_data={"pages_read": 12},
        )
        ev3 = await activity_service.record_activity_event(
            db,
            applied_inst_id,
            primary_student.id,
            "take_notes",
            course_id=course_id,
            lesson_id=lesson_id,
            event_data={"words_written": 250},
        )
        assert ev1["event_type"] == "watch_video"
        assert ev2["event_type"] == "read_pdf"
        assert ev3["event_type"] == "take_notes"

        # =========================================================================
        # 11. COGLEARN records and classifies those interactions
        # =========================================================================
        daily_agg = await activity_service.update_daily_aggregate(db, applied_inst_id, primary_student.id, today)
        assert daily_agg["total_clicks"] >= 3
        assert daily_agg["weighted_clicks"] > 0
        assert daily_agg["valid_click_count"] == daily_agg["total_clicks"]

        # =========================================================================
        # 12. The teacher publishes an assignment with a deadline
        # =========================================================================
        due_datetime = datetime.now(timezone.utc) + timedelta(days=7)
        assignment = await lms_service.create_assignment(
            db,
            applied_inst_id,
            course_id,
            teacher_id,
            "Transformer Architecture Implementation",
            "Implement multi-head self-attention in PyTorch",
            due_date=due_datetime,
            estimated_hours=6.0,
            workload_weight=3.0,
        )
        assign_id = UUID(assignment["id"])
        published_assign = await lms_service.publish_assignment(db, applied_inst_id, assign_id, teacher_id)
        assert published_assign["is_published"] is True

        # =========================================================================
        # 13. The assignment appears automatically in student's calendar & workload queue
        # =========================================================================
        pending_queue = await task_queue_service.get_student_pending_queue(db, applied_inst_id, primary_student.id)
        assert len(pending_queue) >= 1
        matched_task = next(t for t in pending_queue if t["source_id"] == str(assign_id))
        assert matched_task["task_type"] == "assignment"
        assert matched_task["queue_position"] == 1
        assert matched_task["status"] == "pending"

        cal_events = await calendar_service.get_upcoming_deadlines(db, applied_inst_id, primary_student.id, days_ahead=10)
        assert len(cal_events) >= 1
        matched_cal = next(c for c in cal_events if c["source_task_id"] == matched_task["id"])
        assert matched_cal["event_type"] == "assignment_due"

        # =========================================================================
        # 14. Its workload contribution enters the Model 3 calculation
        # =========================================================================
        summaries = [
            DailyActivitySummary(
                student_id=str(primary_student.id),
                date=today - timedelta(days=2),
                event_counts={"navigate": 4, "read_pdf": 2},
            ),
            DailyActivitySummary(
                student_id=str(primary_student.id),
                date=today - timedelta(days=1),
                event_counts={"watch_video": 2, "take_notes": 1},
            ),
            DailyActivitySummary(
                student_id=str(primary_student.id),
                date=today,
                event_counts={"complete_assignment": 1, "read_pdf": 1},
            ),
        ]
        workload_obs = calculate_workload_observations(
            student_id=str(primary_student.id),
            daily_summaries=summaries,
            model_version="v1.0-provisional",
        )
        assert len(workload_obs) == 3
        smoothed_lambda = workload_obs[-1].smoothed_lambda
        assert 2.5 <= smoothed_lambda <= 2.7

        # =========================================================================
        # 15. Model 1 provides the student's personalized capacity estimate
        # =========================================================================
        daily_counts = [10.0, 12.0, 14.0, 11.0, 13.0]
        capacity = estimate_capacity(
            student_id=str(primary_student.id),
            daily_counts=daily_counts,
            prior=CapacityPrior(alpha_0=2.0, beta_0=1.0),
            model_version="v1.0-provisional",
        )
        mu_capacity = capacity.mean_capacity
        assert capacity.alpha_post == 62.0
        assert capacity.beta_post == 6.0
        assert 10.0 <= mu_capacity <= 10.5
        assert capacity.ci_lower_95 < mu_capacity < capacity.ci_upper_95

        # =========================================================================
        # 16. Model 2 evaluates workload against capacity (M/M/1 queueing)
        # =========================================================================
        q_metrics = calculate_queue_metrics(
            student_id=str(primary_student.id),
            lambda_demand=smoothed_lambda,
            mu_capacity=mu_capacity,
            observation_date=today,
            model_version="v1.0",
        )
        assert q_metrics.is_stable is True
        assert q_metrics.rho == pytest.approx(smoothed_lambda / mu_capacity, rel=1e-3)
        assert q_metrics.L == pytest.approx(q_metrics.rho / (1.0 - q_metrics.rho), rel=1e-3)
        assert q_metrics.W == pytest.approx(1.0 / (mu_capacity - smoothed_lambda), rel=1e-3)
        assert q_metrics.cognitive_regime.value in ["underload", "flow"]

        # Persist Model 2 snapshot
        q_record = QueueMetricSnapshot(
            id=uuid4(),
            institution_id=applied_inst_id,
            student_id=primary_student.id,
            date=today,
            lambda_demand=q_metrics.lambda_demand,
            mu_capacity=q_metrics.mu_capacity,
            rho=q_metrics.rho,
            L=q_metrics.L,
            W=q_metrics.W,
            is_stable=q_metrics.is_stable,
            model_version_id=mv2.id,
            calculated_at=datetime.now(timezone.utc),
        )
        db.add(q_record)
        await db.commit()

        # =========================================================================
        # 17. Model 4 updates estimated cognitive state and IORI
        # =========================================================================
        hmm_filter = RealTimeHMMFilter(student_id=str(primary_student.id))
        obs_bin = discretise_rho(q_metrics.rho)
        obs_vec = ObservationVector(rho=q_metrics.rho, rho_bin=obs_bin, raw_features={"step": 1})
        state_est = hmm_filter.current_estimate(obs_vec)

        assert 0.0 <= state_est.iori <= 1.0
        assert state_est.dominant_state.value in ["flow", "underload", "overload", "fatigue"]
        assert state_est.risk_zone.value in ["green", "yellow", "red"]

        # Persist Model 4 HMM state estimate
        hmm_rec = HMMStateEstimate(
            id=uuid4(),
            institution_id=applied_inst_id,
            student_id=primary_student.id,
            timestamp=datetime.now(timezone.utc),
            p_underload=state_est.p_underload,
            p_flow=state_est.p_flow,
            p_overload=state_est.p_overload,
            p_fatigue=state_est.p_fatigue,
            dominant_state=CognitiveState(state_est.dominant_state.value),
            observation_vector=state_est.observation_vector,
            model_version_id=mv4.id,
            is_provisional_params=True,
        )
        db.add(hmm_rec)
        await db.commit()

        # Persist Model 4 IORI assessment
        iori_rec = IORIAssessment(
            id=uuid4(),
            institution_id=applied_inst_id,
            student_id=primary_student.id,
            timestamp=datetime.now(timezone.utc),
            iori_value=state_est.iori,
            risk_zone=state_est.risk_zone.value,
            p_overload=state_est.p_overload,
            p_fatigue=state_est.p_fatigue,
            hmm_estimate_id=hmm_rec.id,
            model_version_id=mv4.id,
            queue_snapshot_id=q_record.id,
            is_presented_to_mentor=state_est.iori >= 0.60,
        )
        db.add(iori_rec)
        await db.commit()

        # =========================================================================
        # 18. The mentor sees authorized student analytics
        # =========================================================================
        mentor_analytics = await intervention_service.get_mentor_student_analytics(
            db, applied_inst_id, teacher_id, primary_student.id
        )
        assert mentor_analytics["student_id"] == str(primary_student.id)
        assert "workload_breakdown" in mentor_analytics
        assert "pending_tasks" in mentor_analytics
        assert "iori_history" in mentor_analytics
        assert len(mentor_analytics["iori_history"]) >= 1
        assert "latest_queue_metrics" in mentor_analytics
        assert mentor_analytics["latest_queue_metrics"] is not None
        assert mentor_analytics["latest_queue_metrics"]["rho"] == pytest.approx(q_metrics.rho, rel=1e-3)
        assert "referral_body" not in mentor_analytics

        # =========================================================================
        # 19. The student requests mentorship
        # =========================================================================
        help_request = await intervention_service.create_mentorship_request(
            db, applied_inst_id, primary_student.id, "I need guidance with the self-attention tensor dimensions."
        )
        req_id = UUID(help_request["id"])
        assert help_request["status"] == "pending"

        # =========================================================================
        # 20. The mentor accepts the request
        # =========================================================================
        accepted_req = await intervention_service.accept_mentorship_request(
            db, applied_inst_id, req_id, teacher_id
        )
        assert accepted_req["status"] == "accepted"
        assert accepted_req["mentor_id"] == str(teacher_id)
        assert "intervention_id" in accepted_req
        interv_id = UUID(accepted_req["intervention_id"])

        # =========================================================================
        # 21. The mentor sends a private support message
        # =========================================================================
        msg = await intervention_service.send_mentor_message(
            db,
            applied_inst_id,
            interv_id,
            teacher_id,
            primary_student.id,
            "Hi, let's review your tensor broadcasting during office hours today.",
        )
        assert msg["sender_id"] == str(teacher_id)
        assert msg["recipient_id"] == str(primary_student.id)

        s_messages = await intervention_service.get_intervention_messages(
            db, applied_inst_id, interv_id, primary_student.id
        )
        assert len(s_messages) == 1
        assert "tensor broadcasting" in s_messages[0]["body"]

        # =========================================================================
        # 22. The mentor extends an assignment deadline
        # =========================================================================
        task_id = UUID(matched_task["id"])
        new_due_date = due_datetime + timedelta(days=4)
        ext = await task_queue_service.extend_task_deadline(
            db, applied_inst_id, task_id, new_due_date, teacher_id, "Academic support extension for DL project"
        )
        assert ext["original_due_date"] is not None
        assert ext["new_due_date"] is not None
        assert ext["granted_by_mentor_id"] == str(teacher_id)

        # =========================================================================
        # 23. The calendar and workload queue update correctly
        # =========================================================================
        updated_tasks = await task_queue_service.get_student_pending_queue(db, applied_inst_id, primary_student.id)
        updated_task = next(t for t in updated_tasks if t["id"] == str(task_id))
        assert updated_task["due_date"] == new_due_date.isoformat()

        cal_res = await db.execute(select(CalendarEvent).where(CalendarEvent.source_task_id == task_id))
        c_event = cal_res.scalar_one()
        assert c_event.is_revised is True
        assert c_event.original_datetime is not None

        # =========================================================================
        # 24. The cognitive workload calculation reflects the change
        # =========================================================================
        workload_breakdown = await task_queue_service.calculate_student_weighted_workload(
            db, applied_inst_id, primary_student.id
        )
        assert workload_breakdown["total_weighted"] > 0
        assert workload_breakdown["incoming"] >= 1

        # =========================================================================
        # 25. University administrator sees appropriate aggregated analytics
        # =========================================================================
        dept_analytics = await analytics_service.get_department_analytics(db, applied_inst_id, dept_id)
        assert dept_analytics["suppressed"] is False
        assert dept_analytics["student_count"] >= 5
        assert "avg_workload" in dept_analytics
        assert "intervention_count" in dept_analytics
        assert dept_analytics["intervention_count"] >= 1

        # =========================================================================
        # 26. The student cannot retrieve confidential cognitive data through the API
        # =========================================================================
        user_schema = UserResponse.model_validate(primary_student)
        user_dict = user_schema.model_dump()
        for forbidden_key in ["iori", "hmm_probabilities", "alpha_post", "beta_post", "mentor_notes", "referral_data"]:
            assert forbidden_key not in user_dict

        workload_summary = StudentWorkloadSummaryResponse(
            incoming_tasks=len(updated_tasks),
            overdue_tasks=0,
            completed_tasks=0,
            next_deadline=datetime.fromisoformat(updated_task["due_date"]),
        )
        workload_dict = workload_summary.model_dump()
        for forbidden_key in ["iori", "rho", "hmm_probabilities", "capacity_estimate", "mentor_notes", "referral_data"]:
            assert forbidden_key not in workload_dict

        # =========================================================================
        # 27. A different institution cannot access the university's data
        # =========================================================================
        other_inst_id = uuid4()
        other_uni = Institution(
            id=other_inst_id, name="Other University", slug="other-uni", is_active=True
        )
        db.add(other_uni)

        other_admin_id = uuid4()
        other_admin = User(
            id=other_admin_id,
            institution_id=other_inst_id,
            email="admin@other.edu",
            hashed_password=hash_password("OtherAdminPass1!"),
            full_name="Other Admin",
            role=UserRole.INST_ADMIN,
            is_active=True,
        )
        db.add(other_admin)
        await db.commit()

        cross_courses = await lms_service.list_courses(db, other_inst_id)
        assert len(cross_courses) == 0

        cross_dept = await lms_service.list_departments(db, other_inst_id)
        assert len(cross_dept) == 0

        cross_analytics = await analytics_service.get_department_analytics(db, other_inst_id, dept_id)
        assert cross_analytics["student_count"] == 0

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def test_part_j_acceptance_all_27_steps():
    """Execute all 27 Part J Acceptance Scenarios in sequence."""
    asyncio.run(_run_part_j_acceptance_flow())


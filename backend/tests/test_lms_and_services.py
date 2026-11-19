"""
Comprehensive tests for LMS Core Services, Task Queue, Calendar, Notifications,
and Intervention Engine.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.services import (
    activity_service,
    analytics_service,
    calendar_service,
    intervention_service,
    lms_service,
    notification_service,
    task_queue_service,
)


async def _run_service_flow():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Setup test institution & users
        inst_id = uuid4()
        inst = Institution(id=inst_id, name="Test University", slug="test-uni", is_active=True)
        db.add(inst)

        teacher_id = uuid4()
        teacher = User(
            id=teacher_id,
            institution_id=inst_id,
            email="prof@test.internal",
            hashed_password="hash",
            full_name="Professor X",
            role=UserRole.TEACHER,
            is_active=True,
        )
        db.add(teacher)

        student_id = uuid4()
        student = User(
            id=student_id,
            institution_id=inst_id,
            email="alice@test.internal",
            hashed_password="hash",
            full_name="Alice Student",
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(student)
        await db.commit()

        # 1. Create Department, Programme, Semester
        dept = await lms_service.create_department(db, inst_id, "Computer Science", "CS")
        assert dept["code"] == "CS"

        prog = await lms_service.create_programme(
            db, inst_id, UUID(dept["id"]), "B.Sc. Computer Science", "BSCS"
        )
        assert prog["name"] == "B.Sc. Computer Science"

        sem = await lms_service.create_semester(
            db, inst_id, "Fall 2026", date(2026, 9, 1), date(2026, 12, 20)
        )
        assert sem["is_active"] is True

        # 2. Create and publish course
        course = await lms_service.create_course(
            db,
            inst_id,
            teacher_id,
            UUID(sem["id"]),
            UUID(dept["id"]),
            "Algorithms",
            "Intro to Algorithms",
        )
        course_id = UUID(course["id"])
        published_course = await lms_service.publish_course(db, inst_id, course_id)
        assert published_course["is_published"] is True

        # 3. Enrol student
        enrolment = await lms_service.enrol_student(db, inst_id, course_id, student_id)
        assert enrolment["status"] == "enrolled"

        # 4. Create and publish assignment
        due_dt = datetime.now(timezone.utc) + timedelta(days=5)
        assignment = await lms_service.create_assignment(
            db,
            inst_id,
            course_id,
            teacher_id,
            "Assignment 1",
            "Sorting algorithms",
            due_dt,
            estimated_hours=2.5,
            workload_weight=1.5,
        )
        assignment_id = UUID(assignment["id"])

        # Publishing must populate task queue and calendar
        pub_assignment = await lms_service.publish_assignment(
            db, inst_id, assignment_id, teacher_id
        )
        assert pub_assignment["is_published"] is True

        # Check student task queue (FIFO order)
        queue = await task_queue_service.get_student_pending_queue(db, inst_id, student_id)
        assert len(queue) == 1
        assert queue[0]["title"] == "Assignment 1"
        assert queue[0]["queue_position"] == 1
        task_id = UUID(queue[0]["id"])

        # Check student calendar event
        cal = await calendar_service.get_upcoming_deadlines(db, inst_id, student_id)
        assert len(cal) == 1
        assert "Assignment 1" in cal[0]["title"]

        # 5. Grant deadline extension
        new_due = due_dt + timedelta(days=3)
        ext = await task_queue_service.extend_task_deadline(
            db, inst_id, task_id, new_due, teacher_id, "Medical exemption"
        )
        assert ext["reason"] == "Medical exemption"

        # Verify calendar revised
        cal_revised = await calendar_service.get_upcoming_deadlines(db, inst_id, student_id, days_ahead=10)
        assert cal_revised[0]["is_revised"] is True

        # 6. Student submits assignment
        submission = await lms_service.submit_assignment(
            db, inst_id, assignment_id, student_id, content_text="Solution code attached"
        )
        assert submission["status"] == "submitted"

        # Queue should now have 0 pending tasks
        pending_queue = await task_queue_service.get_student_pending_queue(
            db, inst_id, student_id
        )
        assert len(pending_queue) == 0

        # 7. Mentorship request flow
        m_req = await intervention_service.create_mentorship_request(
            db, inst_id, student_id, "I need guidance with algorithms."
        )
        assert m_req["status"] == "pending"

        # Teacher accepts mentorship request
        accepted = await intervention_service.accept_mentorship_request(
            db, inst_id, UUID(m_req["id"]), teacher_id
        )
        assert accepted["status"] == "accepted"
        intervention_id = UUID(accepted["intervention_id"])

        # Send message within intervention
        msg = await intervention_service.send_mentor_message(
            db, inst_id, intervention_id, teacher_id, student_id, "Hi Alice, let's meet tomorrow."
        )
        assert msg["body"] == "Hi Alice, let's meet tomorrow."

        # 8. Activity Event and Daily Aggregate flow
        ev = await activity_service.record_activity_event(
            db,
            inst_id,
            student_id,
            event_type="watch_video",
            course_id=course_id,
        )
        assert ev["event_type"] == "watch_video"
        assert ev["is_anomalous"] is False

        aggs = await activity_service.get_daily_aggregates(
            db, inst_id, student_id, date.today() - timedelta(days=1), date.today() + timedelta(days=1)
        )
        assert len(aggs) >= 1
        assert aggs[0]["total_clicks"] >= 1
        assert aggs[0]["weighted_clicks"] > 0

        # 9. Notification flow
        notif = await notification_service.create_notification(
            db,
            inst_id,
            student_id,
            category="academic_announcement",
            title="Class Cancelled",
            body="Tomorrow's lecture is online.",
            priority="high",
        )
        assert notif["title"] == "Class Cancelled"
        unread = await notification_service.get_unread_count(db, inst_id, student_id)
        assert unread >= 1

        marked = await notification_service.mark_notification_read(
            db, inst_id, UUID(notif["id"]), student_id
        )
        assert marked["is_read"] is True

        # 10. Institutional Summary
        summary = await analytics_service.get_institution_summary(db, inst_id)
        assert summary["total_students"] == 1
        assert summary["total_teachers"] == 1
        assert summary["total_courses"] == 1

        # 11. Department analytics (cohort size < MIN_COHORT_SIZE suppresses individual details)
        dept_analytics = await analytics_service.get_department_analytics(
            db, inst_id, UUID(dept["id"])
        )
        assert dept_analytics["suppressed"] is True
        assert "privacy threshold" in dept_analytics["message"]

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def test_lms_and_task_queue_integration():
    """Run end-to-end service integration test."""
    asyncio.run(_run_service_flow())

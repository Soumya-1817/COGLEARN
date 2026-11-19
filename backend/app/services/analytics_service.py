"""
Institutional Analytics Service
================================
Provides aggregate analytics for university administrators.

Privacy protections:
  - Minimum cohort size (default n>=5) before displaying aggregate
  - No individual-level IORI without explicit authorization
  - No simplistic teacher performance rankings from IORI
  - All individual access logged in audit_log
"""

from datetime import date, datetime, timezone
import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.academic_task import AcademicTask, AcademicTaskStatus
from app.models.course import Course
from app.models.deadline_extension import DeadlineExtension
from app.models.department import Department
from app.models.enrolment import CourseEnrolment, EnrolmentStatus
from app.models.intervention import Intervention, InterventionStatus
from app.models.iori_assessment import IORIAssessment, RiskZone
from app.models.programme import Programme
from app.models.semester import Semester
from app.models.submission import Submission
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

MIN_COHORT_SIZE = settings.MIN_COHORT_SIZE


async def get_department_analytics(
    db: AsyncSession,
    institution_id: UUID,
    department_id: Optional[UUID] = None,
    semester_id: Optional[UUID] = None,
) -> dict:
    """
    Aggregate analytics by department.
    Returns: avg_iori, iori_distribution, intervention_count, 
             student_count, avg_workload, overdue_rate
    Suppressed if student_count < MIN_COHORT_SIZE.
    """
    # 1. Enrolled students count in this department's courses
    course_query = select(Course.id).where(
        Course.institution_id == institution_id
    )
    if department_id:
        course_query = course_query.where(Course.department_id == department_id)
    if semester_id:
        course_query = course_query.where(Course.semester_id == semester_id)

    course_ids = (await db.execute(course_query)).scalars().all()

    if not course_ids:
        return {
            "department_id": str(department_id) if department_id else None,
            "student_count": 0,
            "suppressed": True,
            "message": "No courses found for the specified department/semester.",
        }

    students_stmt = select(distinct(CourseEnrolment.student_id)).where(
        and_(
            CourseEnrolment.course_id.in_(course_ids),
            CourseEnrolment.institution_id == institution_id,
            CourseEnrolment.status == EnrolmentStatus.ENROLLED,
        )
    )
    student_ids = (await db.execute(students_stmt)).scalars().all()
    student_count = len(student_ids)

    # Privacy constraint: k-anonymity cohort threshold
    if student_count < MIN_COHORT_SIZE:
        return {
            "department_id": str(department_id) if department_id else None,
            "student_count": student_count,
            "suppressed": True,
            "message": f"Cohort size ({student_count}) is below minimum privacy threshold (n >= {MIN_COHORT_SIZE}). Aggregates suppressed.",
        }

    # 2. Latest IORI assessments for cohort students
    # Use subquery for latest IORI assessment per student
    latest_iori_subq = (
        select(
            IORIAssessment.student_id,
            func.max(IORIAssessment.timestamp).label("max_ts"),
        )
        .where(
            and_(
                IORIAssessment.student_id.in_(student_ids),
                IORIAssessment.institution_id == institution_id,
            )
        )
        .group_by(IORIAssessment.student_id)
        .subquery()
    )

    iori_stats_stmt = (
        select(
            func.avg(IORIAssessment.iori_value).label("avg_iori"),
            func.count(case((IORIAssessment.risk_zone == RiskZone.GREEN, 1))).label("green_count"),
            func.count(case((IORIAssessment.risk_zone == RiskZone.YELLOW, 1))).label("yellow_count"),
            func.count(case((IORIAssessment.risk_zone == RiskZone.RED, 1))).label("red_count"),
        )
        .join(
            latest_iori_subq,
            and_(
                IORIAssessment.student_id == latest_iori_subq.c.student_id,
                IORIAssessment.timestamp == latest_iori_subq.c.max_ts,
            ),
        )
    )
    iori_row = (await db.execute(iori_stats_stmt)).one()
    avg_iori = float(iori_row.avg_iori or 0.0)
    green_count = int(iori_row.green_count or 0)
    yellow_count = int(iori_row.yellow_count or 0)
    red_count = int(iori_row.red_count or 0)

    # 3. Interventions count for cohort
    interventions_stmt = select(func.count(Intervention.id)).where(
        and_(
            Intervention.student_id.in_(student_ids),
            Intervention.institution_id == institution_id,
        )
    )
    intervention_count = (await db.execute(interventions_stmt)).scalar() or 0

    # 4. Workload & Overdue Task Stats
    task_stats_stmt = select(
        func.avg(AcademicTask.estimated_workload * AcademicTask.workload_weight).label("avg_task_load"),
        func.count(AcademicTask.id).label("total_tasks"),
        func.count(case((AcademicTask.status == AcademicTaskStatus.OVERDUE, 1))).label("overdue_tasks"),
    ).where(
        and_(
            AcademicTask.student_id.in_(student_ids),
            AcademicTask.institution_id == institution_id,
        )
    )
    task_row = (await db.execute(task_stats_stmt)).one()
    total_tasks = int(task_row.total_tasks or 0)
    overdue_tasks = int(task_row.overdue_tasks or 0)
    avg_workload = float(task_row.avg_task_load or 0.0)
    overdue_rate = round(overdue_tasks / total_tasks, 4) if total_tasks > 0 else 0.0

    return {
        "department_id": str(department_id) if department_id else None,
        "semester_id": str(semester_id) if semester_id else None,
        "student_count": student_count,
        "suppressed": False,
        "avg_iori": round(avg_iori, 4),
        "iori_distribution": {
            "green": green_count,
            "yellow": yellow_count,
            "red": red_count,
        },
        "intervention_count": intervention_count,
        "avg_workload": round(avg_workload, 2),
        "overdue_rate": overdue_rate,
    }


async def get_programme_analytics(
    db: AsyncSession,
    institution_id: UUID,
    programme_id: Optional[UUID] = None,
    semester_id: Optional[UUID] = None,
) -> dict:
    """Aggregate analytics by study programme."""
    dept_id = None
    if programme_id:
        p_stmt = select(Programme.department_id).where(
            and_(
                Programme.id == programme_id,
                Programme.institution_id == institution_id,
            )
        )
        dept_id = (await db.execute(p_stmt)).scalar_one_or_none()

    res = await get_department_analytics(
        db=db,
        institution_id=institution_id,
        department_id=dept_id,
        semester_id=semester_id,
    )
    res["programme_id"] = str(programme_id) if programme_id else None
    return res


async def get_course_analytics(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
) -> dict:
    """
    Course-level aggregate: workload distribution, submission rate,
    avg IORI trend, intervention count, extension count.
    """
    # 1. Enrolled students
    students_stmt = select(CourseEnrolment.student_id).where(
        and_(
            CourseEnrolment.course_id == course_id,
            CourseEnrolment.institution_id == institution_id,
            CourseEnrolment.status == EnrolmentStatus.ENROLLED,
        )
    )
    student_ids = (await db.execute(students_stmt)).scalars().all()
    student_count = len(student_ids)

    if student_count < MIN_COHORT_SIZE:
        return {
            "course_id": str(course_id),
            "student_count": student_count,
            "suppressed": True,
            "message": f"Course enrollment ({student_count}) is below minimum privacy threshold ({MIN_COHORT_SIZE}). Aggregates suppressed.",
        }

    # 2. Submissions rate
    tasks_count_stmt = select(func.count(AcademicTask.id)).where(
        and_(
            AcademicTask.course_id == course_id,
            AcademicTask.institution_id == institution_id,
        )
    )
    total_assigned_tasks = (await db.execute(tasks_count_stmt)).scalar() or 0

    submissions_stmt = select(func.count(AcademicTask.id)).where(
        and_(
            AcademicTask.course_id == course_id,
            AcademicTask.institution_id == institution_id,
            AcademicTask.status == AcademicTaskStatus.COMPLETED,
        )
    )
    completed_tasks = (await db.execute(submissions_stmt)).scalar() or 0
    submission_rate = (
        round(completed_tasks / total_assigned_tasks, 4) if total_assigned_tasks > 0 else 0.0
    )

    # 3. Interventions count for enrolled students
    interventions_stmt = select(func.count(Intervention.id)).where(
        and_(
            Intervention.student_id.in_(student_ids),
            Intervention.institution_id == institution_id,
        )
    )
    intervention_count = (await db.execute(interventions_stmt)).scalar() or 0

    # 4. Deadline extensions count for course tasks
    ext_stmt = select(func.count(DeadlineExtension.id)).join(
        AcademicTask, AcademicTask.id == DeadlineExtension.task_id
    ).where(
        and_(
            AcademicTask.course_id == course_id,
            DeadlineExtension.institution_id == institution_id,
        )
    )
    extension_count = (await db.execute(ext_stmt)).scalar() or 0

    # 5. Average IORI across students enrolled
    iori_subq = (
        select(
            IORIAssessment.student_id,
            func.max(IORIAssessment.timestamp).label("max_ts"),
        )
        .where(
            and_(
                IORIAssessment.student_id.in_(student_ids),
                IORIAssessment.institution_id == institution_id,
            )
        )
        .group_by(IORIAssessment.student_id)
        .subquery()
    )
    avg_iori_stmt = select(func.avg(IORIAssessment.iori_value)).join(
        iori_subq,
        and_(
            IORIAssessment.student_id == iori_subq.c.student_id,
            IORIAssessment.timestamp == iori_subq.c.max_ts,
        ),
    )
    avg_iori = (await db.execute(avg_iori_stmt)).scalar() or 0.0

    return {
        "course_id": str(course_id),
        "student_count": student_count,
        "suppressed": False,
        "submission_rate": submission_rate,
        "completed_tasks": completed_tasks,
        "total_tasks": total_assigned_tasks,
        "intervention_count": intervention_count,
        "extension_count": extension_count,
        "avg_iori": round(float(avg_iori), 4),
    }


async def get_institution_summary(
    db: AsyncSession,
    institution_id: UUID,
) -> dict:
    """
    Top-level institutional summary:
    - Total students, teachers, courses
    - Active semester stats
    - Aggregate IORI distribution (green/yellow/red counts)
    - Intervention volume
    - Mentorship coverage rate
    """
    # 1. Total Students and Teachers
    student_count_stmt = select(func.count(User.id)).where(
        and_(
            User.institution_id == institution_id,
            User.role == UserRole.STUDENT,
            User.is_active.is_(True),
        )
    )
    total_students = (await db.execute(student_count_stmt)).scalar() or 0

    teacher_count_stmt = select(func.count(User.id)).where(
        and_(
            User.institution_id == institution_id,
            User.role == UserRole.TEACHER,
            User.is_active.is_(True),
        )
    )
    total_teachers = (await db.execute(teacher_count_stmt)).scalar() or 0

    # 2. Courses
    courses_count_stmt = select(func.count(Course.id)).where(
        Course.institution_id == institution_id
    )
    total_courses = (await db.execute(courses_count_stmt)).scalar() or 0

    # 3. Active Semester
    today = date.today()
    sem_stmt = select(Semester.name).where(
        and_(
            Semester.institution_id == institution_id,
            Semester.is_active.is_(True),
            Semester.start_date <= today,
            Semester.end_date >= today,
        )
    ).limit(1)
    active_sem_name = (await db.execute(sem_stmt)).scalar_one_or_none()

    # 4. Latest IORI distribution for all students
    latest_iori_subq = (
        select(
            IORIAssessment.student_id,
            func.max(IORIAssessment.timestamp).label("max_ts"),
        )
        .where(IORIAssessment.institution_id == institution_id)
        .group_by(IORIAssessment.student_id)
        .subquery()
    )

    iori_dist_stmt = (
        select(
            func.count(case((IORIAssessment.risk_zone == RiskZone.GREEN, 1))).label("green_count"),
            func.count(case((IORIAssessment.risk_zone == RiskZone.YELLOW, 1))).label("yellow_count"),
            func.count(case((IORIAssessment.risk_zone == RiskZone.RED, 1))).label("red_count"),
            func.avg(IORIAssessment.iori_value).label("avg_iori"),
        )
        .join(
            latest_iori_subq,
            and_(
                IORIAssessment.student_id == latest_iori_subq.c.student_id,
                IORIAssessment.timestamp == latest_iori_subq.c.max_ts,
            ),
        )
    )
    dist_row = (await db.execute(iori_dist_stmt)).one()
    green_count = int(dist_row.green_count or 0)
    yellow_count = int(dist_row.yellow_count or 0)
    red_count = int(dist_row.red_count or 0)
    avg_iori = float(dist_row.avg_iori or 0.0)

    # 5. Intervention Volume
    interv_stmt = select(func.count(Intervention.id)).where(
        Intervention.institution_id == institution_id
    )
    total_interventions = (await db.execute(interv_stmt)).scalar() or 0

    open_interv_stmt = select(func.count(Intervention.id)).where(
        and_(
            Intervention.institution_id == institution_id,
            Intervention.status.in_([InterventionStatus.OPEN, InterventionStatus.IN_PROGRESS]),
        )
    )
    active_interventions = (await db.execute(open_interv_stmt)).scalar() or 0

    # 6. Mentorship Coverage Rate: Red-zone students with an intervention
    red_students_stmt = select(distinct(IORIAssessment.student_id)).join(
        latest_iori_subq,
        and_(
            IORIAssessment.student_id == latest_iori_subq.c.student_id,
            IORIAssessment.timestamp == latest_iori_subq.c.max_ts,
            IORIAssessment.risk_zone == RiskZone.RED,
        ),
    )
    red_student_ids = (await db.execute(red_students_stmt)).scalars().all()
    if red_student_ids:
        covered_stmt = select(distinct(Intervention.student_id)).where(
            and_(
                Intervention.student_id.in_(red_student_ids),
                Intervention.institution_id == institution_id,
            )
        )
        covered_count = len((await db.execute(covered_stmt)).scalars().all())
        mentorship_coverage = round(covered_count / len(red_student_ids), 4)
    else:
        mentorship_coverage = 1.0

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_courses": total_courses,
        "active_semester": active_sem_name,
        "avg_iori": round(avg_iori, 4),
        "iori_distribution": {
            "green": green_count,
            "yellow": yellow_count,
            "red": red_count,
        },
        "total_interventions": total_interventions,
        "active_interventions": active_interventions,
        "mentorship_coverage_rate": mentorship_coverage,
    }

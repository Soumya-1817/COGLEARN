"""
LMS Core Service
================
Handles CRUD for all academic structural entities:
- Departments, Programmes, Semesters
- Courses, Modules, Lessons
- Enrolments
- Assignments, Quizzes, Assessments
- Submissions

All operations are tenant-scoped (institution_id required).
Publishing an assignment triggers task queue and calendar population.
"""

from datetime import date, datetime, timezone
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_task import AcademicTask, AcademicTaskStatus, AcademicTaskType
from app.models.assessment import Assessment, AssessmentType
from app.models.assignment import Assignment
from app.models.calendar_event import CalendarEvent, CalendarEventType
from app.models.course import Course
from app.models.department import Department
from app.models.enrolment import CourseEnrolment, EnrolmentStatus
from app.models.lesson import Lesson, LessonType
from app.models.module import Module
from app.models.notification import Notification, NotificationCategory, NotificationPriority
from app.models.programme import Programme
from app.models.quiz import Quiz
from app.models.semester import Semester
from app.models.submission import Submission, SubmissionStatus
from app.models.task_status_history import TaskStatusHistory
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
        elif isinstance(val, (datetime, date)):
            res[column.name] = val.isoformat()
        elif hasattr(val, "value"):
            res[column.name] = val.value
        else:
            res[column.name] = val
    return res


def _dispatch_async_workload_recalculation(student_ids: list[UUID] | None = None) -> None:
    """Dispatches background Celery task for Model 3 workload recalculation."""
    try:
        from app.worker.tasks.analytics import run_nightly_workload_calculation
        run_nightly_workload_calculation.delay()
    except Exception as exc:
        logger.warning("Could not dispatch async Celery workload task: %s", exc)


# ---------------------------------------------------------------------------
# Department Operations
# ---------------------------------------------------------------------------

async def create_department(
    db: AsyncSession,
    institution_id: UUID,
    name: str,
    code: str,
    description: str = "",
) -> dict:
    """Creates a new academic department within an institution tenant."""
    dept = Department(
        id=uuid4(),
        institution_id=institution_id,
        name=name.strip(),
        code=code.strip().upper(),
        description=description.strip() if description else None,
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return _model_to_dict(dept)


async def list_departments(db: AsyncSession, institution_id: UUID) -> list[dict]:
    """Lists all academic departments for a given institution tenant."""
    stmt = (
        select(Department)
        .where(Department.institution_id == institution_id)
        .order_by(Department.name.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [_model_to_dict(r) for r in records]


async def get_department(
    db: AsyncSession,
    institution_id: UUID,
    department_id: UUID,
) -> dict:
    """Retrieves a single department by its ID within the institution tenant."""
    stmt = select(Department).where(
        and_(
            Department.id == department_id,
            Department.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()
    if dept is None:
        raise ValueError(f"Department {department_id} not found.")
    return _model_to_dict(dept)


# ---------------------------------------------------------------------------
# Programme Operations
# ---------------------------------------------------------------------------

async def create_programme(
    db: AsyncSession,
    institution_id: UUID,
    department_id: UUID,
    name: str,
    code: str,
    description: Optional[str] = None,
) -> dict:
    """Creates a new academic degree or study programme."""
    # Verify department exists in tenant
    await get_department(db, institution_id, department_id)

    programme = Programme(
        id=uuid4(),
        institution_id=institution_id,
        department_id=department_id,
        name=name.strip(),
        code=code.strip().upper(),
        description=description.strip() if description else None,
    )
    db.add(programme)
    await db.commit()
    await db.refresh(programme)
    return _model_to_dict(programme)


async def list_programmes(
    db: AsyncSession,
    institution_id: UUID,
    department_id: Optional[UUID] = None,
) -> list[dict]:
    """Lists academic programmes within an institution, optionally filtered by department."""
    conditions = [Programme.institution_id == institution_id]
    if department_id:
        conditions.append(Programme.department_id == department_id)

    stmt = select(Programme).where(and_(*conditions)).order_by(Programme.name.asc())
    result = await db.execute(stmt)
    programmes = result.scalars().all()
    return [_model_to_dict(p) for p in programmes]


# ---------------------------------------------------------------------------
# Semester Operations
# ---------------------------------------------------------------------------

async def create_semester(
    db: AsyncSession,
    institution_id: UUID,
    name: str,
    start_date: date,
    end_date: date,
    code: Optional[str] = None,
) -> dict:
    """Creates an academic semester term within the institution tenant."""
    if not code:
        code = name.replace(" ", "-").upper()

    semester = Semester(
        id=uuid4(),
        institution_id=institution_id,
        name=name.strip(),
        code=code.strip(),
        start_date=start_date,
        end_date=end_date,
        is_active=True,
    )
    db.add(semester)
    await db.commit()
    await db.refresh(semester)
    return _model_to_dict(semester)


async def list_semesters(db: AsyncSession, institution_id: UUID) -> list[dict]:
    """Lists all semesters for an institution ordered by start date."""
    stmt = (
        select(Semester)
        .where(Semester.institution_id == institution_id)
        .order_by(Semester.start_date.desc())
    )
    result = await db.execute(stmt)
    semesters = result.scalars().all()
    return [_model_to_dict(s) for s in semesters]


async def get_active_semester(db: AsyncSession, institution_id: UUID) -> dict | None:
    """Retrieves the currently active semester for the tenant."""
    today = date.today()
    stmt = (
        select(Semester)
        .where(
            and_(
                Semester.institution_id == institution_id,
                Semester.is_active.is_(True),
                Semester.start_date <= today,
                Semester.end_date >= today,
            )
        )
        .order_by(Semester.start_date.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    sem = result.scalar_one_or_none()
    if sem is None:
        # Fall back to latest marked active
        fallback_stmt = (
            select(Semester)
            .where(
                and_(
                    Semester.institution_id == institution_id,
                    Semester.is_active.is_(True),
                )
            )
            .order_by(Semester.start_date.desc())
            .limit(1)
        )
        fb_result = await db.execute(fallback_stmt)
        sem = fb_result.scalar_one_or_none()

    return _model_to_dict(sem) if sem else None


# ---------------------------------------------------------------------------
# Course Operations
# ---------------------------------------------------------------------------

async def create_course(
    db: AsyncSession,
    institution_id: UUID,
    teacher_id: UUID,
    semester_id: UUID,
    department_id: UUID,
    title: str,
    description: str = "",
) -> dict:
    """Creates a new academic course."""
    course = Course(
        id=uuid4(),
        institution_id=institution_id,
        teacher_id=teacher_id,
        semester_id=semester_id,
        department_id=department_id,
        title=title.strip(),
        description=description.strip() if description else None,
        is_published=False,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return _model_to_dict(course)


async def list_courses(
    db: AsyncSession,
    institution_id: UUID,
    semester_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
) -> list[dict]:
    """Lists courses filtered by tenant, optional semester, or teacher."""
    conditions = [Course.institution_id == institution_id]
    if semester_id:
        conditions.append(Course.semester_id == semester_id)
    if teacher_id:
        conditions.append(Course.teacher_id == teacher_id)

    stmt = select(Course).where(and_(*conditions)).order_by(Course.created_at.desc())
    result = await db.execute(stmt)
    courses = result.scalars().all()
    return [_model_to_dict(c) for c in courses]


async def get_course(db: AsyncSession, institution_id: UUID, course_id: UUID) -> dict:
    """Retrieves course details."""
    stmt = select(Course).where(
        and_(
            Course.id == course_id,
            Course.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if course is None:
        raise ValueError(f"Course {course_id} not found.")
    return _model_to_dict(course)


async def publish_course(db: AsyncSession, institution_id: UUID, course_id: UUID) -> dict:
    """Publishes a course making its syllabus visible."""
    stmt = (
        update(Course)
        .where(
            and_(
                Course.id == course_id,
                Course.institution_id == institution_id,
            )
        )
        .values(is_published=True)
        .returning(Course)
    )
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if course is None:
        raise ValueError(f"Course {course_id} not found.")
    await db.commit()
    return _model_to_dict(course)


# ---------------------------------------------------------------------------
# Enrolment Operations
# ---------------------------------------------------------------------------

async def enrol_student(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
    student_id: UUID,
) -> dict:
    """Enrols a student in a course."""
    # Check if already enrolled
    stmt = select(CourseEnrolment).where(
        and_(
            CourseEnrolment.course_id == course_id,
            CourseEnrolment.student_id == student_id,
            CourseEnrolment.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        if existing.status != EnrolmentStatus.ENROLLED:
            existing.status = EnrolmentStatus.ENROLLED
            await db.commit()
            await db.refresh(existing)
        return _model_to_dict(existing)

    enrolment = CourseEnrolment(
        id=uuid4(),
        institution_id=institution_id,
        course_id=course_id,
        student_id=student_id,
        status=EnrolmentStatus.ENROLLED,
    )
    db.add(enrolment)
    await db.commit()
    await db.refresh(enrolment)
    return _model_to_dict(enrolment)


async def get_student_courses(
    db: AsyncSession,
    institution_id: UUID,
    student_id: UUID,
) -> list[dict]:
    """Retrieves all active courses enrolled by a student."""
    stmt = (
        select(Course)
        .join(CourseEnrolment, CourseEnrolment.course_id == Course.id)
        .where(
            and_(
                CourseEnrolment.student_id == student_id,
                CourseEnrolment.institution_id == institution_id,
                CourseEnrolment.status == EnrolmentStatus.ENROLLED,
                Course.institution_id == institution_id,
            )
        )
        .order_by(Course.title.asc())
    )
    result = await db.execute(stmt)
    courses = result.scalars().all()
    return [_model_to_dict(c) for c in courses]


async def get_course_students(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
) -> list[dict]:
    """Retrieves all students actively enrolled in a course."""
    stmt = (
        select(User)
        .join(CourseEnrolment, CourseEnrolment.student_id == User.id)
        .where(
            and_(
                CourseEnrolment.course_id == course_id,
                CourseEnrolment.institution_id == institution_id,
                CourseEnrolment.status == EnrolmentStatus.ENROLLED,
            )
        )
        .order_by(User.full_name.asc())
    )
    result = await db.execute(stmt)
    students = result.scalars().all()
    # Mask internal password hash
    sanitized = []
    for s in students:
        d = _model_to_dict(s)
        d.pop("hashed_password", None)
        sanitized.append(d)
    return sanitized


# ---------------------------------------------------------------------------
# Module Operations
# ---------------------------------------------------------------------------

async def create_module(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
    title: str,
    order_index: int = 0,
    description: Optional[str] = None,
) -> dict:
    """Creates a module inside a course."""
    # Verify course
    await get_course(db, institution_id, course_id)

    module = Module(
        id=uuid4(),
        institution_id=institution_id,
        course_id=course_id,
        title=title.strip(),
        order_index=order_index,
        description=description.strip() if description else None,
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return _model_to_dict(module)


async def list_modules(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
) -> list[dict]:
    """Lists modules belonging to a course in order."""
    stmt = (
        select(Module)
        .where(
            and_(
                Module.course_id == course_id,
                Module.institution_id == institution_id,
            )
        )
        .order_by(Module.order_index.asc())
    )
    result = await db.execute(stmt)
    modules = result.scalars().all()
    return [_model_to_dict(m) for m in modules]


# ---------------------------------------------------------------------------
# Lesson Operations
# ---------------------------------------------------------------------------

async def create_lesson(
    db: AsyncSession,
    institution_id: UUID,
    module_id: UUID,
    course_id: UUID,
    title: str,
    lesson_type: str,
    content_url: str,
    duration_minutes: int = 0,
) -> dict:
    """Creates a lesson resource inside a module."""
    lesson = Lesson(
        id=uuid4(),
        institution_id=institution_id,
        course_id=course_id,
        module_id=module_id,
        title=title.strip(),
        lesson_type=LessonType(lesson_type.lower()),
        content_url=content_url.strip() if content_url else None,
        duration_minutes=duration_minutes,
        is_published=False,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return _model_to_dict(lesson)


async def get_lesson(db: AsyncSession, institution_id: UUID, lesson_id: UUID) -> dict:
    """Retrieves a lesson by ID."""
    stmt = select(Lesson).where(
        and_(
            Lesson.id == lesson_id,
            Lesson.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise ValueError(f"Lesson {lesson_id} not found.")
    return _model_to_dict(lesson)


async def publish_lesson(db: AsyncSession, institution_id: UUID, lesson_id: UUID) -> dict:
    """Marks a lesson as published."""
    stmt = (
        update(Lesson)
        .where(
            and_(
                Lesson.id == lesson_id,
                Lesson.institution_id == institution_id,
            )
        )
        .values(is_published=True)
        .returning(Lesson)
    )
    result = await db.execute(stmt)
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise ValueError(f"Lesson {lesson_id} not found.")
    await db.commit()
    return _model_to_dict(lesson)


# ---------------------------------------------------------------------------
# Assignment Operations
# ---------------------------------------------------------------------------

async def create_assignment(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
    teacher_id: UUID,
    title: str,
    description: str,
    due_date: datetime,
    estimated_hours: float,
    workload_weight: float,
    module_id: Optional[UUID] = None,
) -> dict:
    """
    Creates an academic assignment contributing to ICAP workload.
    workload_weight is marked PROVISIONAL until empirical validation.
    """
    assignment = Assignment(
        id=uuid4(),
        institution_id=institution_id,
        course_id=course_id,
        teacher_id=teacher_id,
        module_id=module_id,
        title=title.strip(),
        description=description.strip() if description else None,
        due_date=due_date,
        estimated_hours=estimated_hours,
        workload_weight=workload_weight,  # PROVISIONAL
        is_published=False,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return _model_to_dict(assignment)


async def publish_assignment(
    db: AsyncSession,
    institution_id: UUID,
    assignment_id: UUID,
    teacher_id: UUID,
) -> dict:
    """
    Publish an assignment.
    After publishing:
    1. Mark assignment published
    2. Create academic_tasks for all enrolled students (FIFO queue)
    3. Create calendar_events for all enrolled students
    4. Dispatch new_assignment notifications
    5. Trigger Model 3 workload recalculation for affected students (Celery)
    """
    # 1. Fetch assignment and verify ownership/tenant
    stmt = select(Assignment).where(
        and_(
            Assignment.id == assignment_id,
            Assignment.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise ValueError(f"Assignment {assignment_id} not found.")

    assignment.is_published = True
    assignment.published_at = datetime.now(timezone.utc)

    # Fetch enrolled students
    enrolled_stmt = select(CourseEnrolment.student_id).where(
        and_(
            CourseEnrolment.course_id == assignment.course_id,
            CourseEnrolment.institution_id == institution_id,
            CourseEnrolment.status == EnrolmentStatus.ENROLLED,
        )
    )
    enrolled_res = await db.execute(enrolled_stmt)
    student_ids = enrolled_res.scalars().all()

    # 2 & 3. Create academic_tasks and calendar_events
    for student_id in student_ids:
        # Determine strict FIFO queue position = current max + 1
        pos_stmt = select(func.coalesce(func.max(AcademicTask.queue_position), 0)).where(
            and_(
                AcademicTask.student_id == student_id,
                AcademicTask.institution_id == institution_id,
            )
        )
        pos_res = await db.execute(pos_stmt)
        next_pos = (pos_res.scalar() or 0) + 1

        task = AcademicTask(
            id=uuid4(),
            institution_id=institution_id,
            student_id=student_id,
            course_id=assignment.course_id,
            module_id=assignment.module_id,
            task_type=AcademicTaskType.ASSIGNMENT,
            source_id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            queue_position=next_pos,
            due_date=assignment.due_date,
            estimated_workload=assignment.estimated_hours,
            workload_weight=assignment.workload_weight,  # PROVISIONAL
            status=AcademicTaskStatus.PENDING,
        )
        db.add(task)

        # Audit history for task entry
        history = TaskStatusHistory(
            id=uuid4(),
            institution_id=institution_id,
            task_id=task.id,
            old_status=AcademicTaskStatus.PENDING,
            new_status=AcademicTaskStatus.PENDING,
            changed_by=teacher_id,
            reason="Initial task publication to queue",
        )
        db.add(history)

        # Calendar event
        cal_event = CalendarEvent(
            id=uuid4(),
            institution_id=institution_id,
            student_id=student_id,
            event_type=CalendarEventType.ASSIGNMENT_DUE,
            title=f"Due: {assignment.title}",
            description=assignment.description,
            start_datetime=assignment.due_date,
            end_datetime=assignment.due_date,
            source_task_id=task.id,
            is_revised=False,
            original_datetime=assignment.due_date,
        )
        db.add(cal_event)

        # 4. In-app notification
        notif = Notification(
            id=uuid4(),
            institution_id=institution_id,
            recipient_id=student_id,
            category=NotificationCategory.NEW_ASSIGNMENT,
            title=f"New Assignment: {assignment.title}",
            body=f"A new assignment '{assignment.title}' is due on {assignment.due_date.strftime('%Y-%m-%d %H:%M')}.",
            priority=NotificationPriority.MEDIUM,
            action_url=f"/courses/{assignment.course_id}/assignments/{assignment.id}",
            source_id=assignment.id,
        )
        db.add(notif)

    await db.commit()
    await db.refresh(assignment)

    # 5. Trigger background Model 3 workload recalculation
    _dispatch_async_workload_recalculation(list(student_ids))

    return _model_to_dict(assignment)


async def get_assignment(db: AsyncSession, institution_id: UUID, assignment_id: UUID) -> dict:
    """Retrieves assignment details."""
    stmt = select(Assignment).where(
        and_(
            Assignment.id == assignment_id,
            Assignment.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise ValueError(f"Assignment {assignment_id} not found.")
    return _model_to_dict(assignment)


async def list_course_assignments(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
) -> list[dict]:
    """Lists assignments for a course."""
    stmt = (
        select(Assignment)
        .where(
            and_(
                Assignment.course_id == course_id,
                Assignment.institution_id == institution_id,
            )
        )
        .order_by(Assignment.due_date.asc())
    )
    result = await db.execute(stmt)
    assignments = result.scalars().all()
    return [_model_to_dict(a) for a in assignments]


# ---------------------------------------------------------------------------
# Quiz Operations
# ---------------------------------------------------------------------------

async def create_quiz(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
    teacher_id: UUID,
    title: str,
    due_date: datetime,
    workload_weight: float = 1.2,  # PROVISIONAL
    questions: list = None,
    description: Optional[str] = None,
    time_limit_minutes: Optional[int] = None,
    module_id: Optional[UUID] = None,
) -> dict:
    """Creates a new course quiz."""
    quiz = Quiz(
        id=uuid4(),
        institution_id=institution_id,
        course_id=course_id,
        teacher_id=teacher_id,
        module_id=module_id,
        title=title.strip(),
        description=description.strip() if description else None,
        due_date=due_date,
        time_limit_minutes=time_limit_minutes,
        workload_weight=workload_weight,  # PROVISIONAL
        questions=questions or [],
        is_published=False,
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return _model_to_dict(quiz)


async def publish_quiz(
    db: AsyncSession,
    institution_id: UUID,
    quiz_id: UUID,
    teacher_id: UUID,
) -> dict:
    """Publishes a quiz and populates tasks and calendars for enrolled students."""
    stmt = select(Quiz).where(
        and_(
            Quiz.id == quiz_id,
            Quiz.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise ValueError(f"Quiz {quiz_id} not found.")

    quiz.is_published = True
    quiz.published_at = datetime.now(timezone.utc)

    enrolled_stmt = select(CourseEnrolment.student_id).where(
        and_(
            CourseEnrolment.course_id == quiz.course_id,
            CourseEnrolment.institution_id == institution_id,
            CourseEnrolment.status == EnrolmentStatus.ENROLLED,
        )
    )
    student_ids = (await db.execute(enrolled_stmt)).scalars().all()

    for student_id in student_ids:
        pos_stmt = select(func.coalesce(func.max(AcademicTask.queue_position), 0)).where(
            and_(
                AcademicTask.student_id == student_id,
                AcademicTask.institution_id == institution_id,
            )
        )
        next_pos = ((await db.execute(pos_stmt)).scalar() or 0) + 1

        task = AcademicTask(
            id=uuid4(),
            institution_id=institution_id,
            student_id=student_id,
            course_id=quiz.course_id,
            module_id=quiz.module_id,
            task_type=AcademicTaskType.QUIZ,
            source_id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            queue_position=next_pos,
            due_date=quiz.due_date,
            estimated_workload=quiz.time_limit_minutes / 60.0 if quiz.time_limit_minutes else 0.5,
            workload_weight=quiz.workload_weight,  # PROVISIONAL
            status=AcademicTaskStatus.PENDING,
        )
        db.add(task)

        cal_event = CalendarEvent(
            id=uuid4(),
            institution_id=institution_id,
            student_id=student_id,
            event_type=CalendarEventType.QUIZ_DUE,
            title=f"Quiz Due: {quiz.title}",
            description=quiz.description,
            start_datetime=quiz.due_date,
            end_datetime=quiz.due_date,
            source_task_id=task.id,
            is_revised=False,
            original_datetime=quiz.due_date,
        )
        db.add(cal_event)

        notif = Notification(
            id=uuid4(),
            institution_id=institution_id,
            recipient_id=student_id,
            category=NotificationCategory.NEW_ASSIGNMENT,
            title=f"New Quiz: {quiz.title}",
            body=f"Quiz '{quiz.title}' is scheduled and due on {quiz.due_date.strftime('%Y-%m-%d %H:%M')}.",
            priority=NotificationPriority.MEDIUM,
            action_url=f"/courses/{quiz.course_id}/quizzes/{quiz.id}",
            source_id=quiz.id,
        )
        db.add(notif)

    await db.commit()
    await db.refresh(quiz)
    _dispatch_async_workload_recalculation(list(student_ids))
    return _model_to_dict(quiz)


# ---------------------------------------------------------------------------
# Assessment Operations
# ---------------------------------------------------------------------------

async def create_assessment(
    db: AsyncSession,
    institution_id: UUID,
    course_id: UUID,
    teacher_id: UUID,
    title: str,
    assessment_type: str,
    scheduled_date: datetime,
    workload_weight: float = 2.0,  # PROVISIONAL
    description: Optional[str] = None,
) -> dict:
    """Creates a high-stakes assessment (midterm, final, project)."""
    assessment = Assessment(
        id=uuid4(),
        institution_id=institution_id,
        course_id=course_id,
        teacher_id=teacher_id,
        title=title.strip(),
        assessment_type=AssessmentType(assessment_type.lower()),
        scheduled_date=scheduled_date,
        workload_weight=workload_weight,  # PROVISIONAL
        description=description.strip() if description else None,
        is_published=False,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return _model_to_dict(assessment)


async def publish_assessment(
    db: AsyncSession,
    institution_id: UUID,
    assessment_id: UUID,
    teacher_id: UUID,
) -> dict:
    """Publishes an assessment and distributes tasks and calendar events."""
    stmt = select(Assessment).where(
        and_(
            Assessment.id == assessment_id,
            Assessment.institution_id == institution_id,
        )
    )
    result = await db.execute(stmt)
    assessment = result.scalar_one_or_none()
    if assessment is None:
        raise ValueError(f"Assessment {assessment_id} not found.")

    assessment.is_published = True

    enrolled_stmt = select(CourseEnrolment.student_id).where(
        and_(
            CourseEnrolment.course_id == assessment.course_id,
            CourseEnrolment.institution_id == institution_id,
            CourseEnrolment.status == EnrolmentStatus.ENROLLED,
        )
    )
    student_ids = (await db.execute(enrolled_stmt)).scalars().all()

    for student_id in student_ids:
        pos_stmt = select(func.coalesce(func.max(AcademicTask.queue_position), 0)).where(
            and_(
                AcademicTask.student_id == student_id,
                AcademicTask.institution_id == institution_id,
            )
        )
        next_pos = ((await db.execute(pos_stmt)).scalar() or 0) + 1

        task = AcademicTask(
            id=uuid4(),
            institution_id=institution_id,
            student_id=student_id,
            course_id=assessment.course_id,
            task_type=AcademicTaskType.ASSESSMENT,
            source_id=assessment.id,
            title=assessment.title,
            description=assessment.description,
            queue_position=next_pos,
            due_date=assessment.scheduled_date,
            estimated_workload=3.0,  # default estimated hours for major assessment
            workload_weight=assessment.workload_weight,  # PROVISIONAL
            status=AcademicTaskStatus.PENDING,
        )
        db.add(task)

        cal_event = CalendarEvent(
            id=uuid4(),
            institution_id=institution_id,
            student_id=student_id,
            event_type=CalendarEventType.ASSESSMENT,
            title=f"Assessment: {assessment.title}",
            description=assessment.description,
            start_datetime=assessment.scheduled_date,
            end_datetime=assessment.scheduled_date,
            source_task_id=task.id,
            is_revised=False,
            original_datetime=assessment.scheduled_date,
        )
        db.add(cal_event)

        notif = Notification(
            id=uuid4(),
            institution_id=institution_id,
            recipient_id=student_id,
            category=NotificationCategory.ASSESSMENT_REMINDER,
            title=f"High-Stakes Assessment: {assessment.title}",
            body=f"Assessment '{assessment.title}' is scheduled for {assessment.scheduled_date.strftime('%Y-%m-%d %H:%M')}.",
            priority=NotificationPriority.HIGH,
            action_url=f"/courses/{assessment.course_id}/assessments/{assessment.id}",
            source_id=assessment.id,
        )
        db.add(notif)

    await db.commit()
    await db.refresh(assessment)
    _dispatch_async_workload_recalculation(list(student_ids))
    return _model_to_dict(assessment)


# ---------------------------------------------------------------------------
# Submission Operations
# ---------------------------------------------------------------------------

async def submit_assignment(
    db: AsyncSession,
    institution_id: UUID,
    assignment_id: UUID,
    student_id: UUID,
    content_text: Optional[str] = None,
    content_url: Optional[str] = None,
) -> dict:
    """
    Record a student submission.
    After submission:
    1. Record Submission entity
    2. Update academic_task status to 'completed'
    3. Update calendar_event completion metadata
    4. Dispatch submission notification to teacher
    5. Trigger Model 3 workload recalculation for student
    """
    # Verify assignment
    assignment_stmt = select(Assignment).where(
        and_(
            Assignment.id == assignment_id,
            Assignment.institution_id == institution_id,
        )
    )
    assignment = (await db.execute(assignment_stmt)).scalar_one_or_none()
    if assignment is None:
        raise ValueError(f"Assignment {assignment_id} not found.")

    now = datetime.now(timezone.utc)
    due_norm = assignment.due_date if assignment.due_date.tzinfo else assignment.due_date.replace(tzinfo=timezone.utc)
    submission_status = (
        SubmissionStatus.LATE if now > due_norm else SubmissionStatus.SUBMITTED
    )

    submission = Submission(
        id=uuid4(),
        institution_id=institution_id,
        assignment_id=assignment_id,
        student_id=student_id,
        content_text=content_text,
        content_url=content_url,
        status=submission_status,
        submitted_at=now,
    )
    db.add(submission)

    # Find matching academic task in student queue
    task_stmt = select(AcademicTask).where(
        and_(
            AcademicTask.student_id == student_id,
            AcademicTask.source_id == assignment_id,
            AcademicTask.institution_id == institution_id,
        )
    )
    task = (await db.execute(task_stmt)).scalar_one_or_none()
    if task:
        old_status = task.status
        task.status = AcademicTaskStatus.COMPLETED
        task.completion_timestamp = now
        task.submission_id = submission.id

        history = TaskStatusHistory(
            id=uuid4(),
            institution_id=institution_id,
            task_id=task.id,
            old_status=old_status,
            new_status=AcademicTaskStatus.COMPLETED,
            changed_by=student_id,
            reason="Student submitted work",
        )
        db.add(history)

    # Notify teacher
    teacher_notif = Notification(
        id=uuid4(),
        institution_id=institution_id,
        recipient_id=assignment.teacher_id,
        category=NotificationCategory.ACADEMIC_ANNOUNCEMENT,
        title=f"Submission received: {assignment.title}",
        body=f"A student submitted assignment '{assignment.title}'.",
        priority=NotificationPriority.LOW,
        action_url=f"/assignments/{assignment.id}/submissions/{submission.id}",
        source_id=submission.id,
    )
    db.add(teacher_notif)

    await db.commit()
    await db.refresh(submission)

    _dispatch_async_workload_recalculation([student_id])
    return _model_to_dict(submission)

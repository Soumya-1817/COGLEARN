"""
LMS Core API Router
===================
Endpoints for departments, programmes, semesters, courses, modules,
lessons, assignments, quizzes, assessments, enrolments, and submissions.
All operations are tenant-isolated.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.lms import (
    AssessmentCreate,
    AssessmentResponse,
    AssignmentCreate,
    AssignmentResponse,
    CourseCreate,
    CourseEnrolRequest,
    CourseResponse,
    DepartmentCreate,
    DepartmentResponse,
    EnrolmentResponse,
    LessonCreate,
    LessonResponse,
    ModuleCreate,
    ModuleResponse,
    ProgrammeCreate,
    ProgrammeResponse,
    QuizCreate,
    QuizResponse,
    SemesterCreate,
    SemesterResponse,
    SubmissionCreate,
    SubmissionResponse,
)
from app.services import lms_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all departments in the institution."""
    return await lms_service.list_departments(db, current_user.institution_id)


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_department(
    dept_in: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new department (Admin only)."""
    return await lms_service.create_department(
        db=db,
        institution_id=current_user.institution_id,
        name=dept_in.name,
        code=dept_in.code,
        description=dept_in.description or "",
    )


# ---------------------------------------------------------------------------
# Programmes
# ---------------------------------------------------------------------------

@router.get("/programmes", response_model=list[ProgrammeResponse])
async def list_programmes(
    department_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List programmes, optionally filtered by department."""
    return await lms_service.list_programmes(
        db=db,
        institution_id=current_user.institution_id,
        department_id=department_id,
    )


@router.post(
    "/programmes",
    response_model=ProgrammeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_programme(
    prog_in: ProgrammeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new degree programme (Admin only)."""
    try:
        return await lms_service.create_programme(
            db=db,
            institution_id=current_user.institution_id,
            department_id=prog_in.department_id,
            name=prog_in.name,
            code=prog_in.code,
            description=prog_in.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ---------------------------------------------------------------------------
# Semesters
# ---------------------------------------------------------------------------

@router.get("/semesters", response_model=list[SemesterResponse])
async def list_semesters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List academic semesters."""
    return await lms_service.list_semesters(db, current_user.institution_id)


@router.post(
    "/semesters",
    response_model=SemesterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_semester(
    sem_in: SemesterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an academic semester (Admin only)."""
    return await lms_service.create_semester(
        db=db,
        institution_id=current_user.institution_id,
        name=sem_in.name,
        code=sem_in.code,
        start_date=sem_in.start_date,
        end_date=sem_in.end_date,
    )


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

@router.get("/courses", response_model=list[CourseResponse])
async def list_courses(
    semester_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List courses. If the user is a student, lists their enrolled courses.
    If teacher/admin, lists courses according to filters.
    """
    if current_user.role == UserRole.STUDENT:
        return await lms_service.get_student_courses(
            db=db,
            institution_id=current_user.institution_id,
            student_id=current_user.id,
        )

    return await lms_service.list_courses(
        db=db,
        institution_id=current_user.institution_id,
        semester_id=semester_id,
        teacher_id=teacher_id,
    )


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_course(
    course_in: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new course (Teacher or Admin)."""
    assigned_teacher_id = (
        course_in.teacher_id
        if (course_in.teacher_id and current_user.role in (UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))
        else current_user.id
    )
    return await lms_service.create_course(
        db=db,
        institution_id=current_user.institution_id,
        teacher_id=assigned_teacher_id,
        semester_id=course_in.semester_id,
        department_id=course_in.department_id,
        title=course_in.title,
        description=course_in.description or "",
    )


@router.get(
    "/courses/{id}/students",
    response_model=list[dict],
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def get_course_students(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List students enrolled in course (Teacher/Admin)."""
    return await lms_service.get_course_students(db, current_user.institution_id, id)


@router.post(
    "/courses/{id}/enrol",
    response_model=EnrolmentResponse,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def enrol_student_in_course(
    id: UUID,
    enrol_in: CourseEnrolRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enrol a student in a course (Teacher/Admin)."""
    return await lms_service.enrol_student(
        db=db,
        institution_id=current_user.institution_id,
        course_id=id,
        student_id=enrol_in.student_id,
    )


# ---------------------------------------------------------------------------
# Modules & Lessons
# ---------------------------------------------------------------------------

@router.get("/courses/{id}/modules", response_model=list[ModuleResponse])
async def list_course_modules(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List modules belonging to a course."""
    return await lms_service.list_modules(db, current_user.institution_id, id)


@router.post(
    "/courses/{id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_course_module(
    id: UUID,
    module_in: ModuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a module to a course."""
    try:
        return await lms_service.create_module(
            db=db,
            institution_id=current_user.institution_id,
            course_id=id,
            title=module_in.title,
            order_index=module_in.order_index,
            description=module_in.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/modules/{id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_module_lesson(
    id: UUID,
    lesson_in: LessonCreate,
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a lesson to a module."""
    return await lms_service.create_lesson(
        db=db,
        institution_id=current_user.institution_id,
        module_id=id,
        course_id=course_id,
        title=lesson_in.title,
        lesson_type=lesson_in.lesson_type,
        content_url=lesson_in.content_url or "",
        duration_minutes=lesson_in.duration_minutes,
    )


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@router.get("/courses/{id}/assignments", response_model=list[AssignmentResponse])
async def list_course_assignments(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List assignments for a course."""
    return await lms_service.list_course_assignments(db, current_user.institution_id, id)


@router.post(
    "/courses/{id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_course_assignment(
    id: UUID,
    assignment_in: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an assignment for a course."""
    return await lms_service.create_assignment(
        db=db,
        institution_id=current_user.institution_id,
        course_id=id,
        teacher_id=current_user.id,
        title=assignment_in.title,
        description=assignment_in.description or "",
        due_date=assignment_in.due_date,
        estimated_hours=assignment_in.estimated_hours,
        workload_weight=assignment_in.workload_weight,
        module_id=assignment_in.module_id,
    )


@router.post(
    "/assignments/{id}/publish",
    response_model=AssignmentResponse,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def publish_assignment(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish assignment and distribute tasks/calendar entries."""
    try:
        return await lms_service.publish_assignment(
            db=db,
            institution_id=current_user.institution_id,
            assignment_id=id,
            teacher_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/assignments/{id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assignment(
    id: UUID,
    sub_in: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit work for an assignment."""
    try:
        return await lms_service.submit_assignment(
            db=db,
            institution_id=current_user.institution_id,
            assignment_id=id,
            student_id=current_user.id,
            content_text=sub_in.content_text,
            content_url=sub_in.content_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# Quizzes
# ---------------------------------------------------------------------------

@router.get("/courses/{id}/quizzes", response_model=list[dict])
async def list_course_quizzes(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List quizzes for a course."""
    from sqlalchemy import select
    from app.models.quiz import Quiz
    stmt = select(Quiz).where(
        Quiz.course_id == id,
        Quiz.institution_id == current_user.institution_id,
    ).order_by(Quiz.due_date.asc())
    quizzes = (await db.execute(stmt)).scalars().all()
    return [lms_service._model_to_dict(q) for q in quizzes]


@router.post(
    "/courses/{id}/quizzes",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_course_quiz(
    id: UUID,
    quiz_in: QuizCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a quiz for a course."""
    return await lms_service.create_quiz(
        db=db,
        institution_id=current_user.institution_id,
        course_id=id,
        teacher_id=current_user.id,
        title=quiz_in.title,
        due_date=quiz_in.due_date,
        workload_weight=quiz_in.workload_weight,
        questions=quiz_in.questions,
        description=quiz_in.description,
        time_limit_minutes=quiz_in.time_limit_minutes,
        module_id=quiz_in.module_id,
    )


@router.post(
    "/quizzes/{id}/publish",
    response_model=QuizResponse,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def publish_quiz(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish quiz and push tasks to students."""
    try:
        return await lms_service.publish_quiz(
            db=db,
            institution_id=current_user.institution_id,
            quiz_id=id,
            teacher_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------

@router.get("/courses/{id}/assessments", response_model=list[dict])
async def list_course_assessments(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List major assessments for a course."""
    from sqlalchemy import select
    from app.models.assessment import Assessment
    stmt = select(Assessment).where(
        Assessment.course_id == id,
        Assessment.institution_id == current_user.institution_id,
    ).order_by(Assessment.scheduled_date.asc())
    assessments = (await db.execute(stmt)).scalars().all()
    return [lms_service._model_to_dict(a) for a in assessments]


@router.post(
    "/courses/{id}/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def create_course_assessment(
    id: UUID,
    ass_in: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a high-stakes assessment."""
    return await lms_service.create_assessment(
        db=db,
        institution_id=current_user.institution_id,
        course_id=id,
        teacher_id=current_user.id,
        title=ass_in.title,
        assessment_type=ass_in.assessment_type,
        scheduled_date=ass_in.scheduled_date,
        workload_weight=ass_in.workload_weight,
        description=ass_in.description,
    )


@router.post(
    "/assessments/{id}/publish",
    response_model=AssessmentResponse,
    dependencies=[Depends(require_role(UserRole.TEACHER, UserRole.INST_ADMIN, UserRole.PLATFORM_ADMIN))],
)
async def publish_assessment(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish an assessment to student calendars and queues."""
    try:
        return await lms_service.publish_assessment(
            db=db,
            institution_id=current_user.institution_id,
            assessment_id=id,
            teacher_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

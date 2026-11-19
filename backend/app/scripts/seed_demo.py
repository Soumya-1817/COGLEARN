"""
COGLEARN Demo Data Seed Script
================================
Creates a complete demo institution with:
- 1 institution (Greenfield University, is_demo=True)
- 2 departments (Computer Science, Data Science)
- 3 academic programmes
- 1 active semester
- 3 teacher accounts
- 10 student accounts
- 5 courses
- Activity event history (last 30 days)
- 2 published assignments with due dates
- Academic tasks in student queues
- Calendar events
- Sample notifications
- Enough activity history to run all 4 analytics models

All demo data is clearly labeled: institution.is_demo = True
No hardcoded identities appear in business logic.
The same code paths run with real institutional records.

Usage:
  python -m app.scripts.seed_demo
  python -m app.scripts.seed_demo --reset  (drops and re-creates demo data)
"""

import argparse
import asyncio
from datetime import date, datetime, timedelta
import random
from typing import Optional
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.academic_task import AcademicTask
from app.models.activity_event import ActivityEvent
from app.models.activity_weight_config import ActivityWeightConfig
from app.models.assignment import Assignment
from app.models.calendar_event import CalendarEvent
from app.models.course import Course
from app.models.daily_activity_aggregate import DailyActivityAggregate
from app.models.department import Department
from app.models.enrolment import CourseEnrolment
from app.models.institution import Institution
from app.models.lesson import Lesson
from app.models.model_version import ModelVersion
from app.models.module import Module
from app.models.notification import Notification
from app.models.programme import Programme
from app.models.quiz import Quiz
from app.models.semester import Semester
from app.models.user import User

random.seed(42)  # Reproducible seed

# Demo configuration
DEMO_INSTITUTION = {
    'name': 'Greenfield University',
    'slug': 'greenfield-university',
    'domain': 'greenfield.edu',
}

DEMO_DEPARTMENTS = [
    {'name': 'Department of Computer Science', 'code': 'CS'},
    {'name': 'Department of Data Science', 'code': 'DS'},
]

DEMO_PROGRAMMES = [
    {'name': 'BSc Computer Science', 'code': 'BSCS', 'dept_index': 0},
    {'name': 'BSc Data Science', 'code': 'BSDS', 'dept_index': 1},
    {'name': 'MSc Artificial Intelligence', 'code': 'MSAI', 'dept_index': 1},
]

DEMO_TEACHERS = [
    {'full_name': 'Dr. Alexandra Chen', 'email': 'achen@greenfield.edu'},
    {'full_name': 'Prof. Marcus Williams', 'email': 'mwilliams@greenfield.edu'},
    {'full_name': 'Dr. Priya Sharma', 'email': 'psharma@greenfield.edu'},
]

DEMO_STUDENTS = [
    {'full_name': 'James Okonkwo', 'email': 'jokonkwo@greenfield.edu'},
    {'full_name': 'Sarah Mitchell', 'email': 'smitchell@greenfield.edu'},
    {'full_name': 'Liang Wei', 'email': 'lwei@greenfield.edu'},
    {'full_name': 'Fatima Al-Hassan', 'email': 'falhassan@greenfield.edu'},
    {'full_name': 'Carlos Rivera', 'email': 'crivera@greenfield.edu'},
    {'full_name': 'Aisha Thompson', 'email': 'athompson@greenfield.edu'},
    {'full_name': 'Dimitri Petrov', 'email': 'dpetrov@greenfield.edu'},
    {'full_name': 'Yuki Tanaka', 'email': 'ytanaka@greenfield.edu'},
    {'full_name': 'Amara Diallo', 'email': 'adiallo@greenfield.edu'},
    {'full_name': 'Noah Bergmann', 'email': 'nbergmann@greenfield.edu'},
]

DEMO_COURSES = [
    {'title': 'Introduction to Machine Learning', 'code': 'CS301', 'teacher_index': 0},
    {'title': 'Data Structures and Algorithms', 'code': 'CS201', 'teacher_index': 1},
    {'title': 'Statistical Foundations of AI', 'code': 'DS302', 'teacher_index': 2},
    {'title': 'Python for Data Science', 'code': 'DS101', 'teacher_index': 0},
    {'title': 'Deep Learning Fundamentals', 'code': 'CS401', 'teacher_index': 1},
]

# PROVISIONAL ICAP weights (matches model3_workload.py)
ICAPP_WEIGHTS = [
    ('navigate', 'passive', 0.10),
    ('open_resource', 'passive', 0.20),
    ('watch_video', 'passive', 0.50),
    ('read_pdf', 'active', 0.80),
    ('take_notes', 'active', 1.00),
    ('download', 'active', 0.30),
    ('attempt_quiz', 'constructive', 2.00),
    ('complete_assignment', 'constructive', 3.00),
    ('prepare_project', 'interactive', 4.00),
    ('submit_assessment', 'interactive', 5.00),
    ('login', 'passive', 0.05),
    ('logout', 'passive', 0.00),
]


async def seed_demo(db: AsyncSession, reset: bool = False) -> None:
    print('\n=== COGLEARN Demo Seed Script ===')
    print('Creating Greenfield University demo data...\n')

    if reset:
        print('Resetting demo institution...')
        existing = await db.execute(
            select(Institution).where(Institution.slug == DEMO_INSTITUTION['slug'])
        )
        inst = existing.scalar_one_or_none()
        if inst:
            await db.execute(delete(User).where(User.institution_id == inst.id))
            await db.execute(delete(Institution).where(Institution.id == inst.id))
            await db.commit()
            print('Demo institution reset.')

    # Check if institution already exists
    existing = await db.execute(
        select(Institution).where(Institution.slug == DEMO_INSTITUTION['slug'])
    )
    institution = existing.scalar_one_or_none()
    if institution is None:
        # --- Institution ---
        institution = Institution(
            id=uuid4(),
            name=DEMO_INSTITUTION['name'],
            slug=DEMO_INSTITUTION['slug'],
            domain=DEMO_INSTITUTION['domain'],
            is_demo=True,
            is_active=True,
            approved_at=datetime.utcnow(),
        )
        db.add(institution)
        await db.flush()
        print(f'[+] Institution: {institution.name} (is_demo=True, id={institution.id})')
    else:
        print(f'[*] Existing demo institution found: {institution.name} (id={institution.id})')

    # --- Activity Weight Config ---
    for activity_type, icap_level, weight in ICAPP_WEIGHTS:
        config = ActivityWeightConfig(
            id=uuid4(),
            institution_id=institution.id,
            activity_type=activity_type,
            icap_level=icap_level,
            weight=weight,
            version='v1.0-provisional',
            effective_date=date.today() - timedelta(days=90),
            notes='PROVISIONAL weight - not yet validated by research methodology',
        )
        db.add(config)
    await db.flush()
    print('[+] ICAP activity weight config seeded (v1.0-provisional)')

    # --- Model Version Registry ---
    for model_num, name in [(1, 'Bayesian Capacity'), (2, 'MM1 Queue'), (3, 'ICAP Workload'), (4, 'HMM Cognitive State')]:
        existing_mv = await db.execute(
            select(ModelVersion).where(ModelVersion.model_number == model_num)
        )
        if not existing_mv.scalar_one_or_none():
            mv = ModelVersion(
                id=uuid4(),
                model_number=model_num,
                version_string='v1.0-provisional',
                parameters={'is_provisional': True},
                is_provisional=True,
                effective_from=datetime.utcnow() - timedelta(days=90),
                notes=f'Model {model_num}: {name} - PROVISIONAL parameters',
            )
            db.add(mv)
    await db.flush()
    print('[+] Model version registry seeded')

    # --- Departments ---
    departments = []
    for dept_data in DEMO_DEPARTMENTS:
        dept = Department(
            id=uuid4(),
            institution_id=institution.id,
            name=dept_data['name'],
            code=dept_data['code'],
        )
        db.add(dept)
        departments.append(dept)
    await db.flush()
    print(f'[+] {len(departments)} departments created')

    # --- Programmes ---
    programmes = []
    for prog_data in DEMO_PROGRAMMES:
        prog = Programme(
            id=uuid4(),
            institution_id=institution.id,
            department_id=departments[prog_data['dept_index']].id,
            name=prog_data['name'],
            code=prog_data['code'],
        )
        db.add(prog)
        programmes.append(prog)
    await db.flush()
    print(f'[+] {len(programmes)} programmes created')

    # --- Semester ---
    semester = Semester(
        id=uuid4(),
        institution_id=institution.id,
        name='Autumn Semester 2026',
        code='AUT2026',
        start_date=date(2026, 9, 1),
        end_date=date(2027, 1, 31),
        is_active=True,
    )
    db.add(semester)
    await db.flush()
    print(f'[+] Semester: {semester.name}')

    # --- Teacher/Mentor accounts ---
    teachers = []
    for t_data in DEMO_TEACHERS:
        teacher = User(
            id=uuid4(),
            institution_id=institution.id,
            email=t_data['email'],
            hashed_password=hash_password('DemoTeacher123!'),
            full_name=t_data['full_name'],
            role='teacher',
            is_active=True,
            is_verified=True,
        )
        db.add(teacher)
        teachers.append(teacher)
    await db.flush()
    print(f'[+] {len(teachers)} teacher accounts created')

    # --- Student accounts ---
    students = []
    for s_data in DEMO_STUDENTS:
        student = User(
            id=uuid4(),
            institution_id=institution.id,
            email=s_data['email'],
            hashed_password=hash_password('DemoStudent123!'),
            full_name=s_data['full_name'],
            role='student',
            is_active=True,
            is_verified=True,
        )
        db.add(student)
        students.append(student)
    await db.flush()
    print(f'[+] {len(students)} student accounts created')

    # --- Institution Admin ---
    admin = User(
        id=uuid4(),
        institution_id=institution.id,
        email='admin@greenfield.edu',
        hashed_password=hash_password('DemoAdmin123!'),
        full_name='Admin User',
        role='inst_admin',
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    await db.flush()
    print('[+] Institution admin account created')

    # --- Platform Admin ---
    platform_admin = User(
        id=uuid4(),
        institution_id=None,
        email='admin@coglearn.platform',
        hashed_password=hash_password('PlatformAdmin2026!'),
        full_name='Platform Superadmin',
        role='platform_admin',
        is_active=True,
        is_verified=True,
    )
    db.add(platform_admin)
    await db.flush()
    print('[+] Platform admin account created (admin@coglearn.platform)')

    # --- Courses ---
    courses = []
    for c_data in DEMO_COURSES:
        course = Course(
            id=uuid4(),
            institution_id=institution.id,
            semester_id=semester.id,
            department_id=departments[0].id,
            teacher_id=teachers[c_data['teacher_index']].id,
            title=c_data['title'],
            description=f'Demo course: {c_data["title"]}',
            is_published=True,
        )
        db.add(course)
        courses.append(course)
    await db.flush()
    print(f'[+] {len(courses)} courses created and published')

    # --- Enrolments: all students in all courses ---
    for course in courses:
        for student in students:
            enrolment = CourseEnrolment(
                id=uuid4(),
                institution_id=institution.id,
                course_id=course.id,
                student_id=student.id,
                status='enrolled',
            )
            db.add(enrolment)
    await db.flush()
    print(f'[+] {len(students) * len(courses)} course enrolments created')

    # --- Modules and Lessons ---
    for course in courses[:2]:  # First 2 courses get modules/lessons
        for m_idx in range(3):
            module = Module(
                id=uuid4(),
                institution_id=institution.id,
                course_id=course.id,
                title=f'Module {m_idx + 1}: Core Concepts',
                order_index=m_idx,
            )
            db.add(module)
            await db.flush()

            for l_idx in range(3):
                lesson = Lesson(
                    id=uuid4(),
                    institution_id=institution.id,
                    module_id=module.id,
                    course_id=course.id,
                    title=f'Lesson {l_idx + 1}',
                    lesson_type='video' if l_idx == 0 else 'pdf' if l_idx == 1 else 'text',
                    content_url=f'https://demo.coglearn.app/content/{uuid4()}',
                    duration_minutes=random.randint(15, 60),
                    is_published=True,
                    order_index=l_idx,
                )
                db.add(lesson)
    await db.flush()
    print('[+] Modules and lessons created')

    # --- Assignments ---
    assignments = []
    today = date.today()
    for i, course in enumerate(courses[:3]):
        assignment = Assignment(
            id=uuid4(),
            institution_id=institution.id,
            course_id=course.id,
            teacher_id=course.teacher_id,
            title=f'Assignment {i+1}: {course.title}',
            description='Demo assignment for COGLEARN platform',
            due_date=datetime.combine(today + timedelta(days=7 + i*3), datetime.max.time().replace(hour=23, minute=59)),
            estimated_hours=float(2 + i),
            workload_weight=3.0,  # Constructive ICAP level
            is_published=True,
            published_at=datetime.utcnow() - timedelta(days=3),
        )
        db.add(assignment)
        assignments.append(assignment)
    await db.flush()
    print(f'[+] {len(assignments)} published assignments created')

    # --- Academic Task Queue for each student ---
    queue_pos_tracker = {str(s.id): 0 for s in students}
    for student in students:
        for assignment in assignments:
            queue_pos_tracker[str(student.id)] += 1
            task = AcademicTask(
                id=uuid4(),
                institution_id=institution.id,
                student_id=student.id,
                course_id=assignment.course_id,
                task_type='assignment',
                source_id=assignment.id,
                title=assignment.title,
                description=assignment.description,
                arrival_timestamp=assignment.published_at,
                queue_position=queue_pos_tracker[str(student.id)],  # FIFO
                due_date=assignment.due_date,
                estimated_workload=assignment.estimated_hours,
                workload_weight=assignment.workload_weight,
                status='pending',
            )
            db.add(task)

            # Calendar event
            cal_event = CalendarEvent(
                id=uuid4(),
                institution_id=institution.id,
                student_id=student.id,
                event_type='assignment_due',
                title=f'DUE: {assignment.title}',
                start_datetime=assignment.due_date,
                source_task_id=task.id,
                is_revised=False,
            )
            db.add(cal_event)
    await db.flush()
    print('[+] Academic task queue and calendar events created for all students')

    # --- Activity Events (last 30 days) ---
    event_types = [
        ('navigate', 10), ('open_resource', 5), ('watch_video', 3),
        ('read_pdf', 4), ('take_notes', 2), ('attempt_quiz', 1),
    ]
    icap_weights_dict = {at: w for at, _, w in ICAPP_WEIGHTS}

    for student in students:
        for days_back in range(30, 0, -1):
            event_date = today - timedelta(days=days_back)
            # Vary activity level per student to create different cognitive profiles
            activity_multiplier = random.uniform(0.3, 2.0)
            total_clicks = 0
            weighted_clicks = 0.0

            for event_type, base_count in event_types:
                count = max(0, int(base_count * activity_multiplier + random.gauss(0, 1)))
                for _ in range(count):
                    event = ActivityEvent(
                        id=uuid4(),
                        institution_id=institution.id,
                        student_id=student.id,
                        course_id=random.choice(courses).id,
                        event_type=event_type,
                        event_data={'demo': True},
                        occurred_at=datetime.combine(event_date, datetime.min.time()).replace(
                            hour=random.randint(8, 22),
                            minute=random.randint(0, 59)
                        ),
                        is_anomalous=False,
                    )
                    db.add(event)
                total_clicks += count
                weighted_clicks += count * icap_weights_dict.get(event_type, 0.0)

            # Daily aggregate
            agg = DailyActivityAggregate(
                id=uuid4(),
                institution_id=institution.id,
                student_id=student.id,
                date=event_date,
                total_clicks=total_clicks,
                weighted_clicks=weighted_clicks,
                valid_click_count=total_clicks,
                anomalous_click_count=0,
                session_count=random.randint(1, 4),
                unique_courses_accessed=random.randint(1, min(3, len(courses))),
            )
            db.add(agg)

    await db.flush()
    print('[+] Activity events and daily aggregates created (30 days history)')

    # --- Notifications ---
    for student in students[:3]:  # Sample notifications for first 3 students
        notif = Notification(
            id=uuid4(),
            institution_id=institution.id,
            recipient_id=student.id,
            category='new_assignment',
            title='New Assignment: ' + assignments[0].title,
            body='A new assignment has been published in your course.',
            priority='medium',
            is_read=False,
        )
        db.add(notif)
    await db.flush()

    await db.commit()
    print('\n=== Seed Complete ===')
    print(f'Institution: {institution.name} (is_demo=True)')
    print('Admin login: admin@greenfield.edu / DemoAdmin123!')
    print('Teacher login: achen@greenfield.edu / DemoTeacher123!')
    print('Student login: jokonkwo@greenfield.edu / DemoStudent123!')
    print(f'Students: {len(students)} | Courses: {len(courses)} | Assignments: {len(assignments)}')
    print('\nNote: All demo data is labeled is_demo=True on the institution record.')
    print('Replace with real institutional data via the admin portal.')
    print('The same application code paths process demo and real data identically.')


async def seed_demo_runner(reset: bool = False):
    async with AsyncSessionLocal() as db:
        await seed_demo(db, reset=reset)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed COGLEARN demo data')
    parser.add_argument('--reset', action='store_true', help='Reset existing demo data before seeding')
    args = parser.parse_args()

    asyncio.run(seed_demo_runner(args.reset))

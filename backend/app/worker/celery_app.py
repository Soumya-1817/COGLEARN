from celery import Celery
from celery.schedules import crontab
import os

# Load environment
from dotenv import load_dotenv
load_dotenv()

celery_app = Celery(
    'coglearn',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[
        'app.worker.tasks.analytics',
        'app.worker.tasks.notifications',
        'app.worker.tasks.queue_maintenance',
    ]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # Acknowledge after completion for reliability
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    # Nightly analytics pipeline - runs at 2am UTC
    'nightly-capacity-estimation': {
        'task': 'app.worker.tasks.analytics.run_nightly_capacity_estimation',
        'schedule': crontab(hour=2, minute=0),
    },
    'nightly-workload-calculation': {
        'task': 'app.worker.tasks.analytics.run_nightly_workload_calculation',
        'schedule': crontab(hour=2, minute=15),
    },
    'nightly-iori-assessment': {
        'task': 'app.worker.tasks.analytics.run_nightly_iori_assessment',
        'schedule': crontab(hour=2, minute=30),
    },
    # Queue maintenance - every hour
    'mark-overdue-tasks': {
        'task': 'app.worker.tasks.queue_maintenance.mark_overdue_tasks',
        'schedule': crontab(minute=0),  # top of every hour
    },
    # Deadline reminders - every hour
    'deadline-reminders': {
        'task': 'app.worker.tasks.notifications.send_deadline_reminders',
        'schedule': crontab(minute=30),  # 30 mins past every hour
    },
}

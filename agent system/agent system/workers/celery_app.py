"""
Celery application configuration.
"""

from celery import Celery
from celery.schedules import crontab

from config.settings import settings


celery_app = Celery(
    "academic_resources",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Scheduled tasks (beat)
celery_app.conf.beat_schedule = {
    "crawl-all-courses": {
        "task": "workers.tasks.crawl_all_courses",
        "schedule": crontab(minute=0, hour=f"*/{settings.crawl_interval_hours}"),
    },
}

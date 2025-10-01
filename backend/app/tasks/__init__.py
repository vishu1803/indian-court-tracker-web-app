# backend/app/tasks/__init__.py
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    'court_tracker',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.scraping_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_track_started=True,
    task_serializer='json',
    result_expires=3600,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limit=False,
    task_compression='gzip',
    result_compression='gzip',
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    # Daily cause list update at 6 AM IST
    'daily-cause-list-update': {
        'task': 'app.tasks.scraping_tasks.update_daily_cause_lists',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM IST
        'args': ()
    },
    
    # Weekly cache cleanup at midnight on Sunday
    'weekly-cache-cleanup': {
        'task': 'app.tasks.scraping_tasks.cleanup_old_data',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),  # Sunday midnight
        'args': ()
    },
    
    # Daily statistics update at 11 PM
    'daily-stats-update': {
        'task': 'app.tasks.scraping_tasks.update_daily_statistics',
        'schedule': crontab(hour=23, minute=0),  # 11:00 PM
        'args': ()
    }
}

celery_app.conf.timezone = 'Asia/Kolkata'

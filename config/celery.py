"""
Celery Configuration for Forex Assistant
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')

app = Celery('forex_assistant')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    # Check subscription expiry daily at 9:00 AM
    'check-subscription-expiry-daily': {
        'task': 'apps.accounts.tasks.check_subscription_expiry',
        'schedule': crontab(hour=9, minute=0),
    },
    # Check expired subscriptions daily at 10:00 AM
    'check-expired-subscriptions-daily': {
        'task': 'apps.accounts.tasks.check_expired_subscriptions',
        'schedule': crontab(hour=10, minute=0),
    },
}

# Celery configuration
app.conf.update(
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')

import os
from celery import Celery

# Match settings module exactly
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# If you use django_celery_beat with DB scheduler, define schedules in admin.
# (If you prefer code-based schedule, uncomment below.)
from celery.schedules import crontab
app.conf.beat_schedule = {
    "check-overdue-fees-daily": {
        "task": "finance.tasks.check_overdue_fees_task",
        "schedule": crontab(hour=9, minute=0),  # 9 AM IST
    },
}


app.conf.beat_schedule.update({
    "generate-daily-notifications": {
        "task": "notifications.tasks.generate_daily_notifications",
        "schedule": crontab(hour=10, minute=0),  # runs daily at 10 AM
    },
})
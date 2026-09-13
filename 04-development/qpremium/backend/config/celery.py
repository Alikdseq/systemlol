import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Europe/Moscow schedules from engineering pack
app.conf.timezone = "Europe/Moscow"
app.conf.enable_utc = True
app.conf.beat_schedule = {
    "expire-lots-daily": {
        "task": "loyalty.tasks.expire_lots",
        "schedule": crontab(hour=0, minute=5),
    },
    "warn-expiring-lots-daily": {
        "task": "loyalty.tasks.warn_expiring_lots",
        "schedule": crontab(hour=10, minute=0),
    },
    "birthday-gifts-daily": {
        "task": "loyalty.tasks.grant_birthdays",
        "schedule": crontab(hour=9, minute=0),
    },
    "db-backup-daily": {
        "task": "loyalty.tasks.create_db_backup_task",
        "schedule": crontab(hour=3, minute=0),
    },
}

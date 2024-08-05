from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pcr.settings")
app = Celery("pcr")
app.config_from_object(settings, namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "fetch-pcr-data-schedule": {
        "task": "fetch_pcr.tasks.fetch_pcr_data",
        "schedule": crontab(hour=21, minute=19),
    },
}

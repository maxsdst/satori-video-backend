import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "satori_video.settings.dev")

celery = Celery("satori_video")
celery.config_from_object("django.conf:settings", namespace="CELERY")
celery.autodiscover_tasks()

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .constants import SNAPSHOT_EXPIRATION_TIME_MINUTES
from .models import Snapshot


@shared_task
def cleanup_expired_snapshots() -> None:
    Snapshot.objects.filter(
        creation_date__lt=timezone.now()
        - timedelta(minutes=SNAPSHOT_EXPIRATION_TIME_MINUTES)
    ).delete()

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .constants import NOTIFICATION_EXPIRATION_TIME_DAYS
from .models import Notification


@shared_task
def cleanup_seen_notifications() -> None:
    Notification.objects.filter(
        seen_date__lt=timezone.now() - timedelta(days=NOTIFICATION_EXPIRATION_TIME_DAYS)
    ).delete()

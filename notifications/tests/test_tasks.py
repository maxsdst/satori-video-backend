from time import sleep

import pytest
from django.utils import timezone
from model_bakery import baker

from notifications.constants import NOTIFICATION_EXPIRATION_TIME_DAYS
from notifications.models import Notification
from notifications.tasks import cleanup_seen_notifications


@pytest.mark.django_db
class TestCleanupSeenNotifications:
    def test_deletes_only_expired_seen_notifications(self):
        notification1 = baker.make(Notification, is_seen=False)
        notification2 = baker.make(
            Notification,
            is_seen=True,
            seen_date=timezone.now()
            - timezone.timedelta(days=NOTIFICATION_EXPIRATION_TIME_DAYS),
        )
        notification3 = baker.make(Notification, is_seen=True, seen_date=timezone.now())
        initial_count = Notification.objects.count()
        sleep(0.01)

        cleanup_seen_notifications.apply()

        assert initial_count == 3
        assert Notification.objects.count() == 2
        assert set(x.id for x in Notification.objects.all()) == set(
            [notification1.id, notification3.id]
        )

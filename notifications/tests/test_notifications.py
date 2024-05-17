from time import sleep
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.module_loading import import_string
from model_bakery import baker
from rest_framework import status


NOTIFICATION_MODEL = import_string(list(settings.NOTIFICATION_MODEL_CONFIG.keys())[0])


LIST_VIEWNAME = "notifications:notifications-list"
DETAIL_VIEWNAME = "notifications:notifications-detail"


@pytest.fixture
def create_notification(create_object):
    def _create_notification(notification):
        return create_object(LIST_VIEWNAME, notification, format="json")

    return _create_notification


@pytest.fixture
def retrieve_notification(retrieve_object):
    def _retrieve_notification(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_notification


@pytest.fixture
def update_notification(update_object):
    def _update_notification(pk, notification):
        return update_object(DETAIL_VIEWNAME, pk, notification)

    return _update_notification


@pytest.fixture
def delete_notification(delete_object):
    def _delete_notification(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_notification


@pytest.fixture
def list_notifications(list_objects):
    def _list_notifications(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_notifications


@pytest.fixture
def mark_as_seen(api_client):
    def _mark_as_seen(notification_ids):
        return api_client.post(
            reverse("notifications:notifications-mark-as-seen"),
            {"notification_ids": notification_ids},
            format="json",
        )

    return _mark_as_seen


@pytest.fixture
def unseen_count(api_client):
    def _unseen_count():
        return api_client.get(reverse("notifications:notifications-unseen-count"))

    return _unseen_count


@pytest.mark.django_db
class TestCreateNotification:
    def test_returns_405(self, authenticate, user, create_notification):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_notification({})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestRetrieveNotification:
    def test_returns_405(self, authenticate, user, retrieve_notification):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = retrieve_notification(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestUpdateNotification:
    def test_returns_405(self, authenticate, user, update_notification):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = update_notification(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteNotification:
    def test_if_user_is_anonymous_returns_401(self, delete_notification):
        response = delete_notification(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_notification_doesnt_exist_returns_404(
        self, authenticate, user, delete_notification
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = delete_notification(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_doesnt_own_notification_returns_404(
        self, authenticate, user, other_user, delete_notification
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        notification = baker.make(NOTIFICATION_MODEL, profile=other_profile)

        response = delete_notification(notification.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_owns_notification_returns_204(
        self, authenticate, user, delete_notification
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        notification = baker.make(NOTIFICATION_MODEL, profile=profile)

        response = delete_notification(notification.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestListNotifications:
    def test_if_user_is_anonymous_returns_401(self, list_notifications):
        response = list_notifications()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_200(self, authenticate, user, list_notifications):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        notification = baker.make(NOTIFICATION_MODEL, profile=profile)

        response = list_notifications()

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == notification.id

    def test_user_can_only_get_own_notifications(
        self, authenticate, user, other_user, list_notifications
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        notification1 = baker.make(NOTIFICATION_MODEL, profile=profile)
        notification2 = baker.make(NOTIFICATION_MODEL, profile=other_profile)

        response = list_notifications()

        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == notification1.id

    def test_ordered_by_creation_date(self, authenticate, user, list_notifications):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        notification1 = baker.make(NOTIFICATION_MODEL, profile=profile)
        sleep(0.0001)
        notification2 = baker.make(NOTIFICATION_MODEL, profile=profile)
        sleep(0.0001)
        notification3 = baker.make(NOTIFICATION_MODEL, profile=profile)

        response = list_notifications()

        assert response.data["results"][0]["id"] == notification3.id
        assert response.data["results"][1]["id"] == notification2.id
        assert response.data["results"][2]["id"] == notification1.id

    def test_cursor_pagination(
        self,
        authenticate,
        user,
        list_notifications,
        pagination,
        api_client,
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        notification1 = baker.make(NOTIFICATION_MODEL, profile=profile)
        sleep(0.0001)
        notification2 = baker.make(NOTIFICATION_MODEL, profile=profile)
        sleep(0.0001)
        notification3 = baker.make(NOTIFICATION_MODEL, profile=profile)

        response1 = list_notifications(
            pagination=pagination(type="cursor", page_size=2)
        )
        response2 = api_client.get(response1.data["next"])

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == notification3.id
        assert response1.data["results"][1]["id"] == notification2.id
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == notification1.id


@pytest.mark.django_db
class TestMarkAsSeen:
    def test_if_user_is_anonymous_returns_401(self, mark_as_seen):
        response = mark_as_seen([])

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, mark_as_seen):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = mark_as_seen(123)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["notification_ids"] is not None

    def test_returns_200(self, authenticate, user, mark_as_seen):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = mark_as_seen([])

        assert response.status_code == status.HTTP_200_OK

    def test_marks_notifications_as_seen(
        self, authenticate, user, mark_as_seen, mock_current_datetime
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        notification1 = baker.make(
            NOTIFICATION_MODEL, profile=profile, is_seen=False, seen_date=None
        )
        notification2 = baker.make(
            NOTIFICATION_MODEL, profile=profile, is_seen=False, seen_date=None
        )
        notification3 = baker.make(
            NOTIFICATION_MODEL, profile=profile, is_seen=False, seen_date=None
        )
        seen_date = timezone.datetime(2024, 1, 1, 6, tzinfo=ZoneInfo("UTC"))

        with mock_current_datetime(seen_date):
            response = mark_as_seen([notification1.id, notification3.id])
        notification1.refresh_from_db()
        notification2.refresh_from_db()
        notification3.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert notification1.is_seen == True
        assert notification1.seen_date == seen_date
        assert notification2.is_seen == False
        assert notification2.seen_date == None
        assert notification3.is_seen == True
        assert notification3.seen_date == seen_date

    def test_marks_only_own_notifications(
        self, authenticate, user, other_user, mark_as_seen
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        notification1 = baker.make(
            NOTIFICATION_MODEL, profile=other_profile, is_seen=False, seen_date=None
        )
        notification2 = baker.make(
            NOTIFICATION_MODEL, profile=profile, is_seen=False, seen_date=None
        )

        response = mark_as_seen([notification1.id, notification2.id])
        notification1.refresh_from_db()
        notification2.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert notification1.is_seen == False
        assert notification1.seen_date == None
        assert notification2.is_seen == True


@pytest.mark.django_db
class TestUnseenCount:
    def test_if_user_is_anonymous_returns_401(self, unseen_count):
        response = unseen_count()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_unseen_count(self, authenticate, user, unseen_count):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        baker.make(NOTIFICATION_MODEL, profile=profile, is_seen=False, _quantity=4)

        response = unseen_count()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["unseen_count"] == 4

    def test_counts_only_own_unseen_notifications(
        self, authenticate, user, other_user, unseen_count
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        baker.make(NOTIFICATION_MODEL, profile=profile, is_seen=False, _quantity=2)
        baker.make(NOTIFICATION_MODEL, profile=profile, is_seen=True, _quantity=4)
        baker.make(
            NOTIFICATION_MODEL, profile=other_profile, is_seen=False, _quantity=5
        )

        response = unseen_count()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["unseen_count"] == 2

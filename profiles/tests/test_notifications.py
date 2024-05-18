import pytest
from model_bakery import baker
from rest_framework import status

from profiles.models import Profile, ProfileNotification


LIST_VIEWNAME = "notifications:notifications-list"


@pytest.fixture
def list_notifications(list_objects):
    def _list_notifications(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_notifications


@pytest.mark.django_db
class TestListNotifications:
    def test_returns_profile_notifications(
        self, authenticate, user, list_notifications, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)
        related_profile = baker.make(Profile)
        notification = baker.make(
            ProfileNotification, profile=profile, related_profile=related_profile
        )

        response = list_notifications()

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": notification.id,
            "type": notification.type,
            "subtype": notification.subtype,
            "profile": notification.profile.id,
            "creation_date": isoformat(notification.creation_date),
            "is_seen": notification.is_seen,
            "related_profile": {
                "id": notification.related_profile.id,
                "user": {
                    "id": notification.related_profile.user.id,
                    "username": notification.related_profile.user.username,
                },
                "full_name": notification.related_profile.full_name,
                "description": notification.related_profile.description,
                "avatar": notification.related_profile.avatar,
                "following_count": 0,
                "follower_count": 0,
                "is_following": False,
            },
        }

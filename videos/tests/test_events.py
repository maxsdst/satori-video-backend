from time import sleep, time

import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework import status

from videos.models import Event, Video


LIST_VIEWNAME = "videos:events-list"
DETAIL_VIEWNAME = "videos:events-detail"


@pytest.fixture
def create_event(create_object):
    def _create_event(event):
        return create_object(LIST_VIEWNAME, event)

    return _create_event


@pytest.fixture
def retrieve_event(retrieve_object):
    def _retrieve_event(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_event


@pytest.fixture
def update_event(update_object):
    def _update_event(pk, event):
        return update_object(DETAIL_VIEWNAME, pk, event)

    return _update_event


@pytest.fixture
def delete_event(delete_object):
    def _delete_event(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_event


@pytest.fixture
def list_events(list_objects):
    def _list_events():
        return list_objects(LIST_VIEWNAME)

    return _list_events


@pytest.mark.django_db
class TestCreateEvent:
    def test_if_user_is_anonymous_returns_401(self, create_event):
        response = create_event({"video": 123, "type": "abc"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, create_event):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_event({"video": 123, "type": "abc"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None
        assert response.data["type"] is not None

    def test_if_data_is_valid_returns_200(self, authenticate, user, create_event):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = create_event({"video": video.id, "type": Event.Type.LIKE})

        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.recommender
    def test_feedback_gets_inserted_in_recommender_system(
        self, authenticate, user, create_event, gorse, celery_worker
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        create_event({"video": video.id, "type": Event.Type.LIKE})
        timer = time() + 20
        has_processed = False
        while not has_processed and time() < timer:
            sleep(1)
            feedbacks = gorse.list_feedbacks("", profile.user.id)
            has_processed = len(feedbacks) > 0

        assert len(feedbacks) == 1
        assert feedbacks[0]["FeedbackType"] == Event.Type.LIKE
        assert int(feedbacks[0]["ItemId"]) == video.id
        assert int(feedbacks[0]["UserId"]) == profile.user.id


@pytest.mark.django_db
class TestRetrieveEvent:
    def test_returns_405(self, authenticate, retrieve_event):
        authenticate()

        response = retrieve_event(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestUpdateEvent:
    def test_returns_405(self, authenticate, update_event):
        authenticate()

        response = update_event(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteEvent:
    def test_returns_405(self, authenticate, delete_event):
        authenticate()

        response = delete_event(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListEvents:
    def test_returns_405(self, authenticate, list_events):
        authenticate()

        response = list_events()

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

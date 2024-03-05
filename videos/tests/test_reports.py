import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework import status

from videos.models import Report, Video


LIST_VIEWNAME = "videos:reports-list"
DETAIL_VIEWNAME = "videos:reports-detail"


@pytest.fixture
def create_report(create_object):
    def _create_report(report):
        return create_object(LIST_VIEWNAME, report)

    return _create_report


@pytest.fixture
def retrieve_report(retrieve_object):
    def _retrieve_report(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_report


@pytest.fixture
def update_report(update_object):
    def _update_report(pk, report):
        return update_object(DETAIL_VIEWNAME, pk, report)

    return _update_report


@pytest.fixture
def delete_report(delete_object):
    def _delete_report(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_report


@pytest.fixture
def list_reports(list_objects):
    def _list_reports():
        return list_objects(LIST_VIEWNAME)

    return _list_reports


@pytest.mark.django_db
class TestCreateReport:
    def test_if_user_is_anonymous_returns_401(self, create_report):
        response = create_report({"video": 123, "reason": "abc"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, create_report):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_report({"video": 123, "reason": "abc"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None
        assert response.data["reason"] is not None

    def test_if_data_is_valid_returns_200(self, authenticate, user, create_report):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = create_report(
            {"video": video.id, "reason": Report.Reason.MISINFORMATION}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data is None


@pytest.mark.django_db
class TestRetrieveReport:
    def test_returns_405(self, authenticate, retrieve_report):
        authenticate()

        response = retrieve_report(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestUpdateReport:
    def test_returns_405(self, authenticate, update_report):
        authenticate()

        response = update_report(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteReport:
    def test_returns_405(self, authenticate, delete_report):
        authenticate()

        response = delete_report(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListReports:
    def test_returns_405(self, authenticate, list_reports):
        authenticate()

        response = list_reports()

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

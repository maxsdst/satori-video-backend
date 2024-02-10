import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework import status

from videos.models import Comment, CommentReport


LIST_VIEWNAME = "videos:comment_reports-list"
DETAIL_VIEWNAME = "videos:comment_reports-detail"


@pytest.fixture
def create_comment_report(create_object):
    def _create_comment_report(comment_report):
        return create_object(LIST_VIEWNAME, comment_report)

    return _create_comment_report


@pytest.fixture
def retrieve_comment_report(retrieve_object):
    def _retrieve_comment_report(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_comment_report


@pytest.fixture
def update_comment_report(update_object):
    def _update_comment_report(pk, comment_report):
        return update_object(DETAIL_VIEWNAME, pk, comment_report)

    return _update_comment_report


@pytest.fixture
def delete_comment_report(delete_object):
    def _delete_comment_report(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_comment_report


@pytest.fixture
def list_comment_reports(list_objects):
    def _list_comment_reports():
        return list_objects(LIST_VIEWNAME)

    return _list_comment_reports


@pytest.mark.django_db
class TestCreateCommentReport:
    def test_if_user_is_anonymous_returns_401(self, create_comment_report):
        response = create_comment_report({"comment": 123, "reason": "abc"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(
        self, authenticate, user, create_comment_report
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_comment_report({"comment": 123, "reason": "abc"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["comment"] is not None
        assert response.data["reason"] is not None

    def test_if_data_is_valid_returns_200(
        self, authenticate, user, create_comment_report
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment)

        response = create_comment_report(
            {"comment": comment.id, "reason": CommentReport.Reason.MISINFORMATION}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data is None


@pytest.mark.django_db
class TestRetrieveCommentReport:
    def test_returns_405(self, authenticate, retrieve_comment_report):
        authenticate()

        response = retrieve_comment_report(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestUpdateCommentReport:
    def test_returns_405(self, authenticate, update_comment_report):
        authenticate()

        response = update_comment_report(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteCommentReport:
    def test_returns_405(self, authenticate, delete_comment_report):
        authenticate()

        response = delete_comment_report(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListCommentReports:
    def test_returns_405(self, authenticate, list_comment_reports):
        authenticate()

        response = list_comment_reports()

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

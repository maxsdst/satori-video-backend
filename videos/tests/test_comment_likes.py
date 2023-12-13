import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from videos.models import Comment, CommentLike


LIST_VIEWNAME = "videos:comment_likes-list"
DETAIL_VIEWNAME = "videos:comment_likes-detail"


@pytest.fixture
def create_comment_like(create_object):
    def _create_comment_like(comment_like):
        return create_object(LIST_VIEWNAME, comment_like)

    return _create_comment_like


@pytest.fixture
def retrieve_comment_like(retrieve_object):
    def _retrieve_comment_like(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_comment_like


@pytest.fixture
def update_comment_like(update_object):
    def _update_comment_like(pk, comment_like):
        return update_object(DETAIL_VIEWNAME, pk, comment_like)

    return _update_comment_like


@pytest.fixture
def delete_comment_like(delete_object):
    def _delete_comment_like(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_comment_like


@pytest.fixture
def list_comment_likes(list_objects):
    def _list_comment_likes(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_comment_likes


@pytest.fixture
def remove_like(api_client):
    def _remove_like(comment_id):
        return api_client.post(
            reverse("videos:comment_likes-remove-like"), {"comment": comment_id}
        )

    return _remove_like


@pytest.mark.django_db
class TestCreateCommentLike:
    def test_if_user_is_anonymous_returns_401(self, create_comment_like):
        response = create_comment_like({"comment": 1})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(
        self, authenticate, user, create_comment_like
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_comment_like({"comment": 123})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["comment"] is not None

    def test_if_data_is_valid_returns_201(
        self, authenticate, user, create_comment_like
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment)

        response = create_comment_like({"comment": comment.id})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0

    def test_cannot_create_duplicate_like(
        self, authenticate, user, create_comment_like
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment)

        response1 = create_comment_like({"comment": comment.id})
        response2 = create_comment_like({"comment": comment.id})

        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.data["id"] > 0
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.data["detail"] is not None


@pytest.mark.django_db
class TestRetrieveCommentLike:
    def test_returns_405(self, authenticate, user, retrieve_comment_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = retrieve_comment_like(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestUpdateCommentLike:
    def test_returns_405(self, authenticate, user, update_comment_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = update_comment_like(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteCommentLike:
    def test_returns_405(self, authenticate, user, delete_comment_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = delete_comment_like(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListCommentLikes:
    def test_returns_405(self, authenticate, user, list_comment_likes):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = list_comment_likes()

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestRemoveLike:
    def test_if_user_is_anonymous_returns_401(self, remove_like):
        response = remove_like(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, remove_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_like("a")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["comment"] is not None

    def test_if_comment_doesnt_exist_returns_400(self, authenticate, user, remove_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_like(1)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_like_doesnt_exist_returns_200(self, authenticate, user, remove_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment)

        response = remove_like(comment.id)

        assert response.status_code == status.HTTP_200_OK

    def test_deletes_like(self, authenticate, user, remove_like):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment)
        like = baker.make(CommentLike, comment=comment, profile=profile)

        response = remove_like(comment.id)

        assert response.status_code == status.HTTP_200_OK
        assert not CommentLike.objects.filter(id=like.id).exists()

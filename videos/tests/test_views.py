import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from videos.models import Video, View


@pytest.fixture
def create_view(api_client):
    def do_create_view(view):
        return api_client.post(reverse("videos:views-list"), view)

    return do_create_view


@pytest.fixture
def retrieve_view(api_client):
    def do_retrieve_view(id):
        return api_client.get(reverse("videos:views-detail", kwargs={"pk": id}))

    return do_retrieve_view


@pytest.fixture
def update_view(api_client):
    def do_update_view(id, view):
        return api_client.patch(reverse("videos:views-detail", kwargs={"pk": id}), view)

    return do_update_view


@pytest.fixture
def delete_view(api_client):
    def do_delete_view(id):
        return api_client.delete(reverse("videos:views-detail", kwargs={"pk": id}))

    return do_delete_view


@pytest.fixture
def list_views(api_client):
    def do_list_views():
        return api_client.get(reverse("videos:views-list"))

    return do_list_views


@pytest.mark.django_db
class TestCreateView:
    def test_if_data_is_invalid_returns_400(self, create_view):
        response = create_view({"video": 123})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None

    def test_if_user_is_anonymous_returns_200(self, create_view):
        video = baker.make(Video)

        response = create_view({"video": video.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    def test_if_user_is_authenticated_returns_200(
        self, authenticate, user, create_view
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = create_view({"video": video.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    def test_cannot_immediately_create_duplicate_view(self, create_view):
        video = baker.make(Video)

        response1 = create_view({"video": video.id})
        response2 = create_view({"video": video.id})

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert View.objects.filter(video=video).count() == 1


@pytest.mark.django_db
class TestRetrieveView:
    def test_returns_405(self, retrieve_view):
        response = retrieve_view(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestUpdateView:
    def test_returns_405(self, update_view):
        response = update_view(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteView:
    def test_returns_405(self, delete_view):
        response = delete_view(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListViews:
    def test_returns_405(self, list_views):
        response = list_views()

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

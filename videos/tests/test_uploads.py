from pathlib import Path
from time import sleep, time

import pytest
from celery.contrib.testing.worker import start_worker
from model_bakery import baker
from rest_framework import status
from django.urls import reverse

from videos.models import Upload


MAX_VIDEO_DURATION_SECONDS = 90
CURRENT_FOLDER = Path(__file__).parent


@pytest.fixture
def valid_video(generate_blank_video):
    return generate_blank_video(width=320, height=240, duration=1, format="mp4")


@pytest.fixture
def invalid_video(generate_blank_video):
    return generate_blank_video(width=320, height=240, duration=1, format="mkv")


@pytest.fixture
def too_long_video(generate_blank_video):
    return generate_blank_video(
        width=320, height=240, duration=MAX_VIDEO_DURATION_SECONDS + 1, format="mp4"
    )


@pytest.fixture
def create_upload(api_client):
    def do_create_upload(upload):
        return api_client.post(reverse("uploads-list"), upload, format="multipart")

    return do_create_upload


@pytest.fixture
def retrieve_upload(api_client):
    def do_retrieve_upload(id):
        return api_client.get(reverse("uploads-detail", kwargs={"pk": id}))

    return do_retrieve_upload


@pytest.mark.django_db
class TestCreateUpload:
    def test_if_user_is_anonymous_returns_401(self, create_upload):
        response = create_upload({"file": ""})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, create_upload):
        authenticate()

        response = create_upload({"file": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["file"] is not None

    def test_if_video_extension_is_not_supported_returns_400(
        self, authenticate, create_upload, invalid_video
    ):
        authenticate()

        response = create_upload({"file": invalid_video})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["file"] is not None

    def test_if_video_is_too_long_returns_400(
        self, authenticate, create_upload, too_long_video
    ):
        authenticate()

        response = create_upload({"file": too_long_video})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["file"] is not None

    def test_if_video_is_valid_returns_201(
        self, authenticate, create_upload, valid_video, user
    ):
        authenticate(user=user)

        response = create_upload({"file": valid_video})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0

    @pytest.mark.django_db(transaction=True)
    def test_if_video_is_valid_processing_succeeds(
        self, authenticate, create_upload, valid_video, user, celery_app
    ):
        with start_worker(celery_app):
            authenticate(user=user)

            response = create_upload({"file": valid_video})
            upload_id = response.data["id"]
            upload = Upload.objects.get(id=upload_id)
            timer = time() + 20
            while not upload.is_done and time() < timer:
                upload.refresh_from_db()
                sleep(0.1)

            assert upload.is_done == True
            assert upload.video.id > 0


@pytest.mark.django_db
class TestRetrieveUpload:
    def test_if_user_is_anonymous_returns_401(self, retrieve_upload):
        response = retrieve_upload(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_upload_doesnt_exist_returns_404(self, authenticate, retrieve_upload):
        authenticate()

        response = retrieve_upload(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_upload_exists_and_user_doesnt_own_upload_returns_404(
        self, retrieve_upload, authenticate, user
    ):
        authenticate()
        upload = baker.make(Upload, user=user)

        response = retrieve_upload(upload.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_upload_exists_and_user_owns_upload_returns_200(
        self, retrieve_upload, authenticate, user
    ):
        authenticate(user=user)
        upload = baker.make(Upload, user=user)

        response = retrieve_upload(upload.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": upload.id,
            "user": user.id,
            "video": None,
            "is_done": False,
        }

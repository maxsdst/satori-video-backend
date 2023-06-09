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

            assert upload.video.id > 0

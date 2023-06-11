import random
import shutil
import string
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO, Generator

import ffmpeg
import pytest
from django.apps import apps
from django.conf import settings
from PIL import Image
from rest_framework.test import APIClient


USER_MODEL = apps.get_model(settings.AUTH_USER_MODEL)


@pytest.fixture
def generate_blank_video():
    @contextmanager
    def do_generate_blank_video(
        *, width: int, height: int, duration: int, format: str
    ) -> Generator[BinaryIO, None, None]:
        image = Image.new("RGB", (width, height), color="red")
        image_data = BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / ("output." + format)

            (
                ffmpeg.input("pipe:", loop=1)
                .output(str(output_path), t=duration, pix_fmt="yuv420p", r=1)
                .run(input=image_data.read(), quiet=True)
            )

            with open(output_path, "rb") as file:
                yield file

    return do_generate_blank_video


@pytest.fixture(autouse=True)
def media_root(settings):
    settings.MEDIA_ROOT = settings.BASE_DIR / "media_test"
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    settings.MEDIA_ROOT.mkdir()
    yield
    shutil.rmtree(settings.MEDIA_ROOT)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate(api_client):
    def do_authenticate(*, user=None, is_staff=False):
        if user is None:
            user = USER_MODEL()
        user.is_staff = is_staff
        return api_client.force_authenticate(user)

    return do_authenticate


def create_user():
    username = "".join(random.sample(string.ascii_lowercase, 15))
    password = "password123"
    email = username + "@email.com"
    return USER_MODEL.objects.create(username=username, password=password, email=email)


@pytest.fixture
def user():
    return create_user()


@pytest.fixture
def other_user():
    return create_user()

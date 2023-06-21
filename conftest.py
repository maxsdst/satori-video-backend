import random
import shutil
import string
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pytest
from django.contrib.auth import get_user_model
from PIL import Image, UnidentifiedImageError
from rest_framework.test import APIClient


USER_MODEL = get_user_model()


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


@pytest.fixture(autouse=True)
def media_root(settings):
    settings.MEDIA_ROOT = settings.BASE_DIR / "media_test"
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    settings.MEDIA_ROOT.mkdir()
    yield
    shutil.rmtree(settings.MEDIA_ROOT)


@pytest.fixture
def generate_blank_image():
    def do_generate_blank_image(*, width: int, height: int, format: str) -> BinaryIO:
        image = Image.new("RGB", (width, height), color="red")
        file = BytesIO()
        image.save(file, format=format)
        file.seek(0)
        file.name = "image." + format.lower()
        return file

    return do_generate_blank_image


@pytest.fixture
def is_valid_image():
    def _is_valid_image(input: Path) -> bool:
        try:
            with Image.open(input) as image:
                image.verify()
        except UnidentifiedImageError:
            return False

        return True

    return _is_valid_image

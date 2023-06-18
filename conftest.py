import random
import string

import pytest
from django.contrib.auth import get_user_model
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

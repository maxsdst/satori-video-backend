import random
import shutil
import string
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Literal

import pytest
from django.contrib.auth import get_user_model
from django.core.files import File
from django.urls import reverse
from PIL import Image, UnidentifiedImageError
from rest_framework.test import APIClient, RequestsClient


USER_MODEL = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def requests_client():
    return RequestsClient()


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
def media_root_setting(settings):
    settings.MEDIA_ROOT = settings.BASE_DIR / "media_test"
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    settings.MEDIA_ROOT.mkdir()
    yield
    shutil.rmtree(settings.MEDIA_ROOT)


@pytest.fixture(autouse=True)
def debug_setting(settings):
    settings.DEBUG = True


@pytest.fixture(autouse=True)
def test_setting(settings):
    settings.TEST = True


@pytest.fixture
def generate_blank_image():
    def do_generate_blank_image(
        *, width: int, height: int, format: str, filename: str = "image"
    ) -> BinaryIO:
        image = Image.new("RGB", (width, height), color="red")
        file = BytesIO()
        image.save(file, format=format)
        file.seek(0)
        file.name = filename + "." + format.lower()
        return file

    return do_generate_blank_image


@pytest.fixture
def is_valid_image(requests_client):
    def _is_valid_image(input: str | Path | File) -> bool:
        if isinstance(input, str):
            response = requests_client.get(input)
            input = BytesIO(response.content)

        try:
            with Image.open(input) as image:
                image.verify()
        except UnidentifiedImageError:
            return False

        return True

    return _is_valid_image


@pytest.fixture
def isoformat():
    def _isoformat(datetime: datetime) -> str:
        value = datetime.isoformat()

        if value.endswith("+00:00"):
            value = value[:-6] + "Z"

        return value

    return _isoformat


@dataclass(kw_only=True)
class Filter:
    field: str
    lookup_type: str
    value: str | int | bool


@pytest.fixture
def filter():
    return Filter


@dataclass(kw_only=True)
class Ordering:
    field: str
    direction: Literal["ASC", "DESC"]


@pytest.fixture
def ordering():
    return Ordering


@dataclass(kw_only=True)
class LimitOffsetPagination:
    limit: int = None
    offset: int = None


@dataclass(kw_only=True)
class SnapshotPagination:
    page_size: int = None
    cursor: str = None


@pytest.fixture
def pagination():
    def _pagination(type: Literal["limit_offset", "snapshot"], **kwargs):
        match type:
            case "limit_offset":
                return LimitOffsetPagination(**kwargs)
            case "snapshot":
                return SnapshotPagination(**kwargs)
            case _:
                raise Exception("Unknown pagination type")

    return _pagination


def apply_filters(filters: list[Filter], query: dict):
    for filter in filters:
        key = (
            filter.field
            if filter.lookup_type == "exact"
            else f"{filter.field}__{filter.lookup_type}"
        )
        query[key] = filter.value


def apply_ordering(ordering: Ordering, query: dict):
    prefix = "-" if ordering.direction == "DESC" else ""
    query["ordering"] = prefix + ordering.field


def apply_pagination(
    pagination: LimitOffsetPagination | SnapshotPagination, query: dict
):
    if isinstance(pagination, LimitOffsetPagination):
        if pagination.limit is not None:
            query["limit"] = pagination.limit
        if pagination.offset is not None:
            query["offset"] = pagination.offset
    elif isinstance(pagination, SnapshotPagination):
        if pagination.page_size is not None:
            query["page_size"] = pagination.page_size
        if pagination.cursor is not None:
            query["cursor"] = pagination.cursor
    else:
        raise Exception("Unknown pagination class")


def build_query(
    *,
    filters: list[Filter] = None,
    ordering: Ordering = None,
    pagination: LimitOffsetPagination | SnapshotPagination = None,
) -> dict[str, str]:
    query = {}

    if filters:
        apply_filters(filters, query)
    if ordering:
        apply_ordering(ordering, query)
    if pagination:
        apply_pagination(pagination, query)

    return query


@pytest.fixture
def create_object(api_client):
    def _create_object(viewname, object, **kwargs):
        return api_client.post(reverse(viewname), object, **kwargs)

    return _create_object


@pytest.fixture
def retrieve_object(api_client):
    def _retrieve_object(viewname, pk, **kwargs):
        return api_client.get(reverse(viewname, kwargs={"pk": pk}), **kwargs)

    return _retrieve_object


@pytest.fixture
def update_object(api_client):
    def _update_object(viewname, pk, object, **kwargs):
        return api_client.patch(reverse(viewname, kwargs={"pk": pk}), object, **kwargs)

    return _update_object


@pytest.fixture
def delete_object(api_client):
    def _delete_object(viewname, pk, **kwargs):
        return api_client.delete(reverse(viewname, kwargs={"pk": pk}), **kwargs)

    return _delete_object


@pytest.fixture
def list_objects(api_client):
    def _list_objects(
        viewname, *, filters=None, ordering=None, pagination=None, **kwargs
    ):
        query = build_query(filters=filters, ordering=ordering, pagination=pagination)
        return api_client.get(reverse(viewname), query, **kwargs)

    return _list_objects

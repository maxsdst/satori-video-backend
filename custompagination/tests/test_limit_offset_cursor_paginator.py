from urllib.parse import parse_qs, urlparse

import pytest
from model_bakery import baker
from rest_framework import status

from custompagination.tests.models import Item


LIST_VIEWNAME = "custompagination_tests:items_limit_offset_cursor_paginator-list"


@pytest.fixture
def list_items(list_objects):
    def _list_items(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_items


def get_cursor(url: str) -> str:
    result = urlparse(url)
    return parse_qs(result.query)["cursor"][0]


def get_next_cursor(response):
    return get_cursor(response.data["next"])


def get_prev_cursor(response):
    return get_cursor(response.data["previous"])


@pytest.mark.django_db
class TestLimitOffsetCursorPaginator:
    def test_items_are_paginated(self, list_items):
        items = baker.make(Item, _quantity=5)

        response = list_items()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["next"] is not None
        assert response.data["previous"] is None
        assert response.data["results"] == [
            {"id": items[0].id, "number": items[0].number},
            {"id": items[1].id, "number": items[1].number},
        ]

    def test_cursor(self, list_items, pagination):
        items = baker.make(Item, _quantity=5)

        response1 = list_items()
        response2 = list_items(
            pagination=pagination(type="cursor", cursor=get_next_cursor(response1))
        )
        response3 = list_items(
            pagination=pagination(type="cursor", cursor=get_next_cursor(response2))
        )
        response4 = list_items(
            pagination=pagination(type="cursor", cursor=get_prev_cursor(response3))
        )
        response5 = list_items(
            pagination=pagination(type="cursor", cursor=get_prev_cursor(response4))
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_200_OK
        assert response4.status_code == status.HTTP_200_OK
        assert response5.status_code == status.HTTP_200_OK
        assert response1.data["results"] == [
            {"id": items[0].id, "number": items[0].number},
            {"id": items[1].id, "number": items[1].number},
        ]
        assert response2.data["results"] == [
            {"id": items[2].id, "number": items[2].number},
            {"id": items[3].id, "number": items[3].number},
        ]
        assert response3.data["results"] == [
            {"id": items[4].id, "number": items[4].number},
        ]
        assert response4.data["results"] == [
            {"id": items[2].id, "number": items[2].number},
            {"id": items[3].id, "number": items[3].number},
        ]
        assert response5.data["results"] == [
            {"id": items[0].id, "number": items[0].number},
            {"id": items[1].id, "number": items[1].number},
        ]

    def test_next_and_previous_links(self, list_items, api_client):
        items = baker.make(Item, _quantity=5)

        response1 = list_items()
        response2 = api_client.get(response1.data["next"])
        response3 = api_client.get(response2.data["next"])
        response4 = api_client.get(response3.data["previous"])
        response5 = api_client.get(response4.data["previous"])

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_200_OK
        assert response4.status_code == status.HTTP_200_OK
        assert response5.status_code == status.HTTP_200_OK
        assert response1.data["previous"] is None
        assert response1.data["results"] == [
            {"id": items[0].id, "number": items[0].number},
            {"id": items[1].id, "number": items[1].number},
        ]
        assert response2.data["results"] == [
            {"id": items[2].id, "number": items[2].number},
            {"id": items[3].id, "number": items[3].number},
        ]
        assert response3.data["next"] is None
        assert response3.data["results"] == [
            {"id": items[4].id, "number": items[4].number},
        ]
        assert response4.data["results"] == [
            {"id": items[2].id, "number": items[2].number},
            {"id": items[3].id, "number": items[3].number},
        ]
        assert response5.data["previous"] is None
        assert response5.data["results"] == [
            {"id": items[0].id, "number": items[0].number},
            {"id": items[1].id, "number": items[1].number},
        ]

    def test_setting_page_size(self, list_items, pagination):
        baker.make(Item, _quantity=5)
        page_size = 4

        response = list_items(pagination=pagination(type="cursor", page_size=page_size))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == page_size
        assert response.data["next"] is not None

    def test_page_size_is_limited(self, list_items, pagination):
        baker.make(Item, _quantity=20)
        page_size = 15

        response = list_items(pagination=pagination(type="cursor", page_size=page_size))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) < page_size
        assert response.data["next"] is not None

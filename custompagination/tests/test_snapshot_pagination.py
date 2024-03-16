from datetime import timedelta
from time import sleep
from urllib.parse import parse_qs, urlparse

import pytest
from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from custompagination.constants import SNAPSHOT_EXPIRATION_TIME_MINUTES
from custompagination.models import Snapshot
from custompagination.tasks import cleanup_expired_snapshots
from custompagination.tests.models import Item


LIST_VIEWNAME = "custompagination_tests:items_snapshot_pagination-list"


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
class TestSnapshotPagination:
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

    def test_order_is_stable(self, list_items, ordering, pagination, api_client):
        items = [baker.make(Item, number=i + 1) for i in range(5)]
        items[3].number = 1000
        items[3].save()
        initial_order = list(
            Item.objects.order_by("number").values_list("id", flat=True)
        )

        response1 = list_items(
            ordering=ordering(field="number", direction="ASC"),
            pagination=pagination(type="cursor", page_size=2),
        )
        items[1].number = 100
        items[4].number = 0
        Item.objects.bulk_update(items, ["number"])
        order = list(Item.objects.order_by("number").values_list("id", flat=True))
        response2 = api_client.get(response1.data["next"])
        response3 = api_client.get(response2.data["next"])

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_200_OK
        assert order != initial_order
        assert [
            response1.data["results"][0]["id"],
            response1.data["results"][1]["id"],
            response2.data["results"][0]["id"],
            response2.data["results"][1]["id"],
            response3.data["results"][0]["id"],
        ] == initial_order

    def test_periodic_task_deletes_expired_snapshots(self):
        snapshot1 = baker.make(Snapshot)
        sleep(0.1)
        with freeze_time(
            timezone.now() + timedelta(minutes=SNAPSHOT_EXPIRATION_TIME_MINUTES)
        ):
            sleep(0.1)
            snapshot2 = baker.make(Snapshot)

            cleanup_expired_snapshots.apply()
            snapshot_ids = list(Snapshot.objects.values_list("id", flat=True))

        assert snapshot1.id not in snapshot_ids
        assert snapshot2.id in snapshot_ids

import json
from base64 import b64decode, b64encode
from collections import OrderedDict
from dataclasses import dataclass

from django.db.models import QuerySet
from django.db.models.sql.where import WhereNode
from rest_framework.exceptions import NotFound
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils.urls import replace_query_param

from ..models import Snapshot


def get_objects_by_primary_keys(queryset: QuerySet, primary_keys: list) -> list:
    """
    Get objects from the provided queryset by a list of primary keys, preserving the order of keys.
    All filters from the queryset will be removed. Non-existent primary keys will be skipped.
    """

    # remove ordering
    queryset = queryset.order_by()
    # remove filters
    queryset.query.where = WhereNode()

    objects = queryset.in_bulk(primary_keys)
    return [objects[pk] for pk in primary_keys if pk in objects]


@dataclass(kw_only=True)
class Cursor:
    snapshot_id: int
    pk: int


class SnapshotPagination(BasePagination):
    """A pagination style that keeps the same order of items as they were fetched in the initial request."""

    page_size = api_settings.PAGE_SIZE
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"

    # Set to an integer to limit the maximum page size the client may request.
    max_page_size = None

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request

        page_size = self.get_page_size()
        if not page_size:
            return None

        self.base_url = request.build_absolute_uri()

        self.cursor = self.decode_cursor()

        self.snapshot = self.get_or_create_snapshot(queryset)

        if not self.cursor:
            self.cursor = Cursor(
                snapshot_id=self.snapshot.id, pk=self.snapshot.primary_keys[0]
            )

        self.cursor_pk_index = self.snapshot.primary_keys.index(self.cursor.pk)

        return self._get_results(queryset)

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )

    def get_or_create_snapshot(self, queryset: QuerySet) -> Snapshot:
        if not self.cursor:
            # first request
            return self.create_snapshot(queryset)

        # following requests
        try:
            return Snapshot.objects.get(id=self.cursor.snapshot_id)
        except Snapshot.DoesNotExist:
            # snapshot expired
            return self.create_snapshot(queryset)

    def _get_results(self, queryset: QuerySet) -> list:
        if not self.snapshot.primary_keys:
            return []

        pks = self.snapshot.primary_keys[
            self.cursor_pk_index : self.cursor_pk_index + self.get_page_size()
        ]
        return get_objects_by_primary_keys(queryset, pks)

    def get_page_size(self) -> int:
        if self.page_size_query_param:
            try:
                page_size = int(self.request.query_params[self.page_size_query_param])
                if self.max_page_size:
                    return min(page_size, self.max_page_size)
                return page_size
            except (KeyError, ValueError):
                pass

        return self.page_size

    def create_snapshot(self, queryset: QuerySet) -> Snapshot:
        pks = list(queryset.values_list("pk", flat=True))
        return Snapshot.objects.create(primary_keys=pks)

    def encode_cursor(self, cursor: Cursor) -> str:
        string = json.dumps({"sid": cursor.snapshot_id, "pk": cursor.pk})
        return b64encode(string.encode("ascii")).decode("ascii")

    def decode_cursor(self) -> Cursor | None:
        encoded = self.request.query_params.get(self.cursor_query_param)
        if encoded is None:
            return None

        try:
            string = b64decode(encoded.encode("ascii")).decode("ascii")
            d = json.loads(string)
            snapshot_id, pk = d["sid"], d["pk"]
        except (TypeError, ValueError, KeyError):
            raise NotFound("Invalid cursor")

        return Cursor(snapshot_id=snapshot_id, pk=pk)

    def get_next_cursor(self) -> Cursor | None:
        next_pk_index = self.cursor_pk_index + self.get_page_size()

        try:
            return Cursor(
                snapshot_id=self.snapshot.id,
                pk=self.snapshot.primary_keys[next_pk_index],
            )
        except IndexError:
            return None

    def get_previous_cursor(self) -> Cursor | None:
        if self.cursor_pk_index == 0:
            return None

        prev_pk_index = max(self.cursor_pk_index - self.get_page_size(), 0)
        return Cursor(
            snapshot_id=self.snapshot.id, pk=self.snapshot.primary_keys[prev_pk_index]
        )

    def get_next_link(self) -> str | None:
        next_cursor = self.get_next_cursor()
        if not next_cursor:
            return None

        return replace_query_param(
            self.base_url, self.cursor_query_param, self.encode_cursor(next_cursor)
        )

    def get_previous_link(self) -> str | None:
        prev_cursor = self.get_previous_cursor()
        if not prev_cursor:
            return None

        return replace_query_param(
            self.base_url, self.cursor_query_param, self.encode_cursor(prev_cursor)
        )

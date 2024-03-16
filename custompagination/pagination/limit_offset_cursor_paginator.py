import json
from base64 import b64decode, b64encode
from collections import OrderedDict
from dataclasses import dataclass

from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils.urls import replace_query_param


@dataclass(kw_only=True)
class Cursor:
    limit: int
    offset: int


class LimitOffsetCursorPaginator:
    """Cursor-based paginator that uses limit and offset under the hood."""

    default_page_size = api_settings.PAGE_SIZE
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"

    # Set to an integer to limit the maximum page size the client may request.
    max_page_size = None

    def __init__(self, request: Request) -> None:
        self._request = request
        self._base_url = request.build_absolute_uri()

        self._page_size = self._get_page_size()

        self._cursor = self._decode_cursor()
        if not self._cursor:
            self._cursor = Cursor(limit=self._page_size, offset=0)

    @property
    def limit(self) -> int:
        return self._page_size

    @property
    def offset(self) -> int:
        return self._cursor.offset

    def get_paginated_response(self, data: list) -> Response:
        return Response(
            OrderedDict(
                [
                    ("next", self._get_next_link(data)),
                    ("previous", self._get_previous_link()),
                    ("results", data),
                ]
            )
        )

    def _get_page_size(self) -> int:
        if self.page_size_query_param:
            try:
                page_size = int(self._request.query_params[self.page_size_query_param])
                if self.max_page_size:
                    return min(page_size, self.max_page_size)
                return page_size
            except (KeyError, ValueError):
                pass

        return self.default_page_size

    def _encode_cursor(self, cursor: Cursor) -> str:
        string = json.dumps({"l": cursor.limit, "o": cursor.offset})
        return b64encode(string.encode("ascii")).decode("ascii")

    def _decode_cursor(self) -> Cursor | None:
        encoded = self._request.query_params.get(self.cursor_query_param)
        if encoded is None:
            return None

        try:
            string = b64decode(encoded.encode("ascii")).decode("ascii")
            d = json.loads(string)
            limit, offset = d["l"], d["o"]
        except (TypeError, ValueError, KeyError):
            raise NotFound("Invalid cursor")

        return Cursor(limit=limit, offset=offset)

    def _get_next_cursor(self, data: list) -> Cursor | None:
        if len(data) < self._cursor.limit:
            return None

        limit = self._page_size
        offset = self._cursor.offset + limit
        return Cursor(limit=limit, offset=offset)

    def _get_previous_cursor(self) -> Cursor | None:
        if self._cursor.offset == 0:
            return None

        limit = self._page_size
        offset = max(0, self._cursor.offset - limit)
        return Cursor(limit=limit, offset=offset)

    def _get_next_link(self, data: list) -> str | None:
        next_cursor = self._get_next_cursor(data)
        if not next_cursor:
            return None

        return replace_query_param(
            self._base_url, self.cursor_query_param, self._encode_cursor(next_cursor)
        )

    def _get_previous_link(self) -> str | None:
        prev_cursor = self._get_previous_cursor()
        if not prev_cursor:
            return None

        return replace_query_param(
            self._base_url, self.cursor_query_param, self._encode_cursor(prev_cursor)
        )

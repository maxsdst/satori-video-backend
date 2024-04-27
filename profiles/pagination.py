from rest_framework.pagination import CursorPagination

from custompagination.pagination import SnapshotPagination


class ProfileSearchPagination(SnapshotPagination):
    max_page_size = 50


class FollowPagination(CursorPagination):
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = "-creation_date"

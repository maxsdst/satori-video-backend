from rest_framework.pagination import CursorPagination

from custompagination.pagination import LimitOffsetCursorPaginator, SnapshotPagination


class CommentPagination(SnapshotPagination):
    max_page_size = 20


class VideoRecommendationPaginator(LimitOffsetCursorPaginator):
    max_page_size = 10


class VideoSearchPagination(SnapshotPagination):
    max_page_size = 50


class HistoryPagination(CursorPagination):
    ordering = "-creation_date"
    max_page_size = 50
    page_size_query_param = "page_size"

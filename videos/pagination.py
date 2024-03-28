from custompagination.pagination import LimitOffsetCursorPaginator, SnapshotPagination


class CommentPagination(SnapshotPagination):
    max_page_size = 20


class VideoRecommendationPaginator(LimitOffsetCursorPaginator):
    max_page_size = 10


class VideoSearchPagination(SnapshotPagination):
    max_page_size = 50

from custompagination.pagination import LimitOffsetCursorPaginator, SnapshotPagination


class ItemSnapshotPagination(SnapshotPagination):
    page_size = 2
    max_page_size = 10


class ItemLimitOffsetCursorPaginator(LimitOffsetCursorPaginator):
    default_page_size = 2
    max_page_size = 10

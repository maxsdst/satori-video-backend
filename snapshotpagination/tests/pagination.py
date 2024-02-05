from snapshotpagination.pagination import SnapshotPagination


class ItemPagination(SnapshotPagination):
    page_size = 2
    max_page_size = 10

from snapshotpagination.pagination import SnapshotPagination


class CommentPagination(SnapshotPagination):
    max_page_size = 20

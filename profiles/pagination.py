from rest_framework.pagination import CursorPagination


class ProfilePagination(CursorPagination):
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = "id"


class FollowPagination(CursorPagination):
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = "-creation_date"

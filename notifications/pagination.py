from rest_framework.pagination import CursorPagination


class NotificationPagination(CursorPagination):
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = "-creation_date"

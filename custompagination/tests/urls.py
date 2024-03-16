from rest_framework.routers import DefaultRouter

from .views import (
    ItemViewSet_LimitOffsetCursorPaginator,
    ItemViewSet_SnapshotPagination,
)


app_name = "custompagination_tests"

router = DefaultRouter()
router.register(
    "items_snapshot_pagination",
    ItemViewSet_SnapshotPagination,
    basename="items_snapshot_pagination",
)
router.register(
    "items_limit_offset_cursor_paginator",
    ItemViewSet_LimitOffsetCursorPaginator,
    basename="items_limit_offset_cursor_paginator",
)

urlpatterns = router.urls

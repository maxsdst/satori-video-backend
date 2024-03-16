from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from .models import Item
from .pagination import ItemLimitOffsetCursorPaginator, ItemSnapshotPagination
from .serializers import ItemSerializer


class ItemViewSet_SnapshotPagination(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [OrderingFilter]
    pagination_class = ItemSnapshotPagination


class ItemViewSet_LimitOffsetCursorPaginator(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def list(self, request, *args, **kwargs):
        paginator = ItemLimitOffsetCursorPaginator(request)
        limit, offset = paginator.limit, paginator.offset

        queryset = self.get_queryset()
        items = list(queryset[offset : offset + limit])

        serializer = self.get_serializer(items, many=True)
        return paginator.get_paginated_response(serializer.data)

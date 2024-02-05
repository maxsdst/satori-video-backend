from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from .models import Item
from .pagination import ItemPagination
from .serializers import ItemSerializer


class ItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [OrderingFilter]
    pagination_class = ItemPagination

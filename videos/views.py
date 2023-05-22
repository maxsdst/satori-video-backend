from rest_framework.viewsets import ModelViewSet

from .models import Video
from .serializers import VideoSerializer


class VideoViewSet(ModelViewSet):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

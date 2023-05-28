from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Upload, Video
from .serializers import CreateUploadSerializer, UploadSerializer, VideoSerializer
from .tasks import handle_upload


class VideoViewSet(ModelViewSet):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class UploadViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUploadSerializer
        return UploadSerializer

    def get_serializer_context(self):
        return {"user_id": self.request.user.id}

    def get_queryset(self):
        user = self.request.user
        return Upload.objects.filter(user_id=user.id)

    @transaction.atomic()
    def create(self, request: Request, *args, **kwargs):
        serializer = CreateUploadSerializer(
            data=request.data, context={"user_id": self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        upload: Upload = serializer.save()

        handle_upload.delay(upload.id, self.request.user.id)

        serializer = UploadSerializer(upload)
        return Response(serializer.data)

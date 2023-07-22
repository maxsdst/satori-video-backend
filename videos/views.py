from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Upload, Video
from .permissions import UserOwnsObjectOrReadOnly
from .serializers import CreateUploadSerializer, UploadSerializer, VideoSerializer
from .tasks import handle_upload


class VideoViewSet(ModelViewSet):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [UserOwnsObjectOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["profile"]


class UploadViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUploadSerializer
        return UploadSerializer

    def get_serializer_context(self):
        return {"profile_id": self.request.user.profile.id}

    def get_queryset(self):
        profile = self.request.user.profile
        return Upload.objects.filter(profile_id=profile.id)

    @transaction.atomic()
    def create(self, request: Request, *args, **kwargs):
        serializer = CreateUploadSerializer(
            data=request.data, context={"profile_id": self.request.user.profile.id}
        )
        serializer.is_valid(raise_exception=True)
        upload: Upload = serializer.save()

        handle_upload.delay(upload.id, self.request.user.profile.id)

        serializer = UploadSerializer(upload)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

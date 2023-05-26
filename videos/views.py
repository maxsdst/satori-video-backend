from pathlib import Path

from django.conf import settings
from django.db import transaction
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Upload, Video
from .serializers import CreateUploadSerializer, UploadSerializer, VideoSerializer
from .utils import create_thumbnail, get_media_url, make_hls


class VideoViewSet(ModelViewSet):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class UploadViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    queryset = Upload.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUploadSerializer
        return UploadSerializer

    def get_serializer_context(self):
        return {"user_id": self.request.user.id}

    @transaction.atomic()
    def create(self, request: Request, *args, **kwargs):
        serializer = CreateUploadSerializer(
            data=request.data, context={"user_id": self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        upload: Upload = serializer.save()

        video = Video.objects.create(
            user_id=self.request.user.id,
            title="",
            description="",
            source="",
            thumbnail="",
        )

        video_path = Path(upload.file.path)
        output_folder = settings.MEDIA_ROOT / "videos" / str(video.id)

        hls_playlist_path = make_hls(video_path, output_folder)
        video.source = get_media_url(hls_playlist_path)

        thumbnail_path = create_thumbnail(video_path, output_folder)
        video.thumbnail = get_media_url(thumbnail_path)

        video.save()

        upload.video = video
        upload.save()

        serializer = UploadSerializer(upload)
        return Response(serializer.data)

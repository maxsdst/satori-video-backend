from pathlib import Path

from django.db import transaction
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .constants import TEMP_FOLDER, VIDEOS_FOLDER
from .models import Upload, Video
from .serializers import CreateUploadSerializer, UploadSerializer, VideoSerializer
from .utils import create_thumbnail, create_vertical_video, get_media_url, make_hls


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

        video = Video.objects.create(
            user_id=self.request.user.id,
            title="",
            description="",
            source="",
            thumbnail="",
        )

        upload_path = Path(upload.file.path)
        video_path = TEMP_FOLDER / upload_path.name

        try:
            create_vertical_video(upload_path, video_path)

            output_folder = VIDEOS_FOLDER / str(video.id)

            hls_playlist_path = make_hls(video_path, output_folder)
            video.source = get_media_url(hls_playlist_path)

            thumbnail_path = create_thumbnail(video_path, output_folder)
            video.thumbnail = get_media_url(thumbnail_path)
        finally:
            video_path.unlink(missing_ok=True)

        video.save()

        upload.video = video
        upload.save()

        serializer = UploadSerializer(upload)
        return Response(serializer.data)

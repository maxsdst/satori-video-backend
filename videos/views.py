from datetime import timedelta

from django.db import transaction
from django.db.models import Prefetch
from django.db.models.aggregates import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .constants import VIEW_COUNT_COOLDOWN_SECONDS
from .models import Upload, Video, View
from .permissions import UserOwnsObjectOrReadOnly
from .serializers import (
    CreateUploadSerializer,
    CreateViewSerializer,
    UploadSerializer,
    VideoSerializer,
)
from .tasks import handle_upload


VIDEO_QUERYSET = (
    Video.objects.select_related("profile__user")
    .annotate(view_count=Count("views"))
    .all()
)


class VideoViewSet(ModelViewSet):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    queryset = VIDEO_QUERYSET
    serializer_class = VideoSerializer
    permission_classes = [UserOwnsObjectOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "profile": ["exact"],
        "title": ["icontains"],
        "description": ["icontains"],
    }
    ordering_fields = ["title", "upload_date", "view_count"]


class UploadViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "filename": ["icontains"],
        "is_done": ["exact"],
    }
    ordering_fields = ["filename", "creation_date", "is_done"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUploadSerializer
        return UploadSerializer

    def get_serializer_context(self):
        return {"request": self.request, "profile_id": self.request.user.profile.id}

    def get_queryset(self):
        profile = self.request.user.profile
        return Upload.objects.filter(profile_id=profile.id).prefetch_related(
            Prefetch("video", VIDEO_QUERYSET)
        )

    @transaction.atomic()
    def create(self, request: Request, *args, **kwargs):
        serializer = CreateUploadSerializer(
            data=request.data, context={"profile_id": self.request.user.profile.id}
        )
        serializer.is_valid(raise_exception=True)
        upload: Upload = serializer.save()

        handle_upload.delay(upload.id, self.request.user.profile.id)

        serializer = UploadSerializer(upload, context={"request": self.request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ViewViewSet(ModelViewSet):
    http_method_names = ["post", "options"]
    serializer_class = CreateViewSerializer

    def create(self, request: Request, *args, **kwargs):
        serializer = CreateViewSerializer(
            data=request.data,
            context={
                "profile_id": (
                    request.user.profile.id if request.user.is_authenticated else None
                ),
                "session_id": self.request.session["id"],
            },
        )
        serializer.is_valid(raise_exception=True)

        video_id = serializer.validated_data["video"]

        if not has_viewed_video(
            request, video_id, timedelta(seconds=VIEW_COUNT_COOLDOWN_SECONDS)
        ):
            serializer.save()

        return Response(status=status.HTTP_200_OK)


def has_viewed_video(request: Request, video_id: int, period: timedelta) -> bool:
    """Check if the sender of the request has viewed a video over a given period of time."""

    views = View.objects.filter(
        video_id=video_id,
        creation_date__range=(timezone.now() - period, timezone.now()),
    )

    user = request.user
    if user.is_authenticated:
        return views.filter(profile_id=user.profile.id).exists()

    session_id = request._request.session["id"]
    return views.filter(session_id=session_id).exists()

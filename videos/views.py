from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, transaction
from django.db.models import (
    Case,
    Model,
    OuterRef,
    Prefetch,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.aggregates import Count
from django.db.models.manager import BaseManager
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .constants import VIEW_COUNT_COOLDOWN_SECONDS
from .filters import CommentFilter, VideoFilter
from .models import Comment, CommentLike, Like, SavedVideo, Upload, Video, View
from .pagination import CommentPagination
from .permissions import UserOwnsObjectOrReadOnly
from .serializers import (
    CommentLikeSerializer,
    CommentSerializer,
    CreateCommentLikeSerializer,
    CreateCommentReportSerializer,
    CreateCommentSerializer,
    CreateLikeSerializer,
    CreateSavedVideoSerializer,
    CreateUploadSerializer,
    CreateViewSerializer,
    LikeSerializer,
    SavedVideoSerializer,
    UploadSerializer,
    VideoSerializer,
)
from .tasks import handle_upload
from .utils import has_any_filter_applied


def get_video_queryset(request: Request) -> BaseManager[Video]:
    queryset = (
        Video.objects.select_related("profile__user")
        .annotate(view_count=count_related_objects_in_subquery(Video, "views"))
        .annotate(like_count=count_related_objects_in_subquery(Video, "likes"))
        .annotate(comment_count=count_related_objects_in_subquery(Video, "comments"))
    )
    queryset = annotate_videos_with_like_status(queryset, request.user)
    queryset = annotate_videos_with_saved_status(queryset, request.user)
    return queryset


def count_related_objects_in_subquery(model: Model, related_name: str) -> Subquery:
    """Generate a subquery to count related objects for each instance of the given model."""

    return Subquery(
        model.objects.filter(pk=OuterRef("pk"))
        .annotate(count=Count(related_name, distinct=True))
        .values("count")
    )


def annotate_videos_with_like_status(
    queryset: QuerySet, user: AbstractUser
) -> QuerySet:
    """Annotate the given video queryset with a field indicating whether the user has liked each video."""

    if not user.is_authenticated:
        return queryset.annotate(is_liked=Value(False))

    liked_video_ids = Like.objects.filter(profile=user.profile).values_list("video_id")

    return queryset.annotate(
        is_liked=Case(
            When(id__in=liked_video_ids, then=Value(True)),
            default=Value(False),
        )
    )


def annotate_videos_with_saved_status(
    queryset: QuerySet, user: AbstractUser
) -> QuerySet:
    """Annotate the given video queryset with a field indicating whether the user has saved each video."""

    if not user.is_authenticated:
        return queryset.annotate(is_saved=Value(False))

    saved_video_ids = SavedVideo.objects.filter(profile=user.profile).values_list(
        "video_id"
    )

    return queryset.annotate(
        is_saved=Case(
            When(id__in=saved_video_ids, then=Value(True)),
            default=Value(False),
        )
    )


def annotate_comments_with_like_status(
    queryset: QuerySet, user: AbstractUser
) -> QuerySet:
    """Annotate the given comment queryset with a field indicating whether the user has liked each comment."""

    if not user.is_authenticated:
        return queryset.annotate(is_liked=Value(False))

    liked_comment_ids = CommentLike.objects.filter(profile=user.profile).values_list(
        "comment_id"
    )

    return queryset.annotate(
        is_liked=Case(
            When(id__in=liked_comment_ids, then=Value(True)),
            default=Value(False),
        )
    )


class VideoViewSet(ModelViewSet):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    serializer_class = VideoSerializer
    permission_classes = [UserOwnsObjectOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = VideoFilter
    ordering_fields = ["title", "upload_date", "view_count", "like_count"]

    def get_queryset(self):
        return get_video_queryset(self.request)


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
            Prefetch("video", get_video_queryset(self.request))
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


class LikeViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAuthenticatedOrReadOnly, UserOwnsObjectOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "video": ["exact"],
        "profile": ["exact"],
    }
    ordering_fields = ["creation_date"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateLikeSerializer
        return LikeSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        return (
            Like.objects.select_related("profile__user")
            .prefetch_related(Prefetch("video", get_video_queryset(self.request)))
            .all()
        )

    @transaction.atomic()
    def create(self, request: Request, *args, **kwargs):
        serializer = CreateLikeSerializer(
            data=request.data, context={"profile_id": self.request.user.profile.id}
        )
        serializer.is_valid(raise_exception=True)

        try:
            like = serializer.save()
        except IntegrityError:
            raise ParseError(detail="You have already liked this video")

        like = self.get_queryset().get(pk=like.id)
        serializer = LikeSerializer(like, context={"request": self.request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        if not has_any_filter_applied(request, ["video", "profile"], self):
            raise PermissionDenied(detail="You must provide a video or profile filter")
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def remove_like(self, request: Request):
        profile = request.user.profile

        serializer = CreateLikeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        video_id = serializer.data["video"]

        Like.objects.filter(video__pk=video_id, profile=profile).delete()

        return Response(status=status.HTTP_200_OK)


class CommentViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [IsAuthenticatedOrReadOnly, UserOwnsObjectOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CommentFilter
    ordering_fields = ["creation_date", "popularity_score"]
    pagination_class = CommentPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateCommentSerializer
        return CommentSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        queryset = (
            Comment.objects.select_related("profile__user")
            .annotate(reply_count=count_related_objects_in_subquery(Comment, "replies"))
            .annotate(like_count=count_related_objects_in_subquery(Comment, "likes"))
        )
        return annotate_comments_with_like_status(queryset, self.request.user)

    def create(self, request: Request, *args, **kwargs):
        serializer = CreateCommentSerializer(
            data=request.data, context={"profile_id": self.request.user.profile.id}
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        comment = self.get_queryset().get(pk=comment.id)
        serializer = CommentSerializer(comment, context={"request": self.request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        if not has_any_filter_applied(request, ["video", "parent"], self):
            raise PermissionDenied(detail="You must provide a video or parent filter")

        return super().list(request, *args, **kwargs)


class CommentLikeViewSet(ModelViewSet):
    http_method_names = ["post", "options"]
    serializer_class = CommentLikeSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request: Request, *args, **kwargs):
        serializer = CreateCommentLikeSerializer(
            data=request.data, context={"profile_id": request.user.profile.id}
        )
        serializer.is_valid(raise_exception=True)

        try:
            like = serializer.save()
        except IntegrityError:
            raise ParseError(detail="You have already liked this comment")

        serializer = CommentLikeSerializer(like, context={"request": self.request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def remove_like(self, request: Request):
        profile = request.user.profile

        serializer = CreateCommentLikeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment_id = serializer.data["comment"]

        CommentLike.objects.filter(comment__pk=comment_id, profile=profile).delete()

        return Response(status=status.HTTP_200_OK)


class CommentReportViewSet(ModelViewSet):
    http_method_names = ["post", "options"]
    serializer_class = CreateCommentReportSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request: Request, *args, **kwargs):
        serializer = CreateCommentReportSerializer(
            data=request.data,
            context={"profile_id": request.user.profile.id},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_200_OK)


class SavedVideoViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["creation_date"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateSavedVideoSerializer
        return SavedVideoSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        profile = self.request.user.profile
        return (
            SavedVideo.objects.select_related("profile__user")
            .prefetch_related(Prefetch("video", get_video_queryset(self.request)))
            .filter(profile_id=profile.id)
            .all()
        )

    @transaction.atomic()
    def create(self, request: Request, *args, **kwargs):
        serializer = CreateSavedVideoSerializer(
            data=request.data, context={"profile_id": self.request.user.profile.id}
        )
        serializer.is_valid(raise_exception=True)

        try:
            saved_video = serializer.save()
        except IntegrityError:
            raise ParseError(detail="You have already saved this video")

        saved_video = self.get_queryset().get(pk=saved_video.id)
        serializer = SavedVideoSerializer(
            saved_video, context={"request": self.request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def remove_video_from_saved(self, request: Request):
        profile = request.user.profile

        serializer = CreateSavedVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        video_id = serializer.data["video"]

        SavedVideo.objects.filter(video__pk=video_id, profile=profile).delete()

        return Response(status=status.HTTP_200_OK)

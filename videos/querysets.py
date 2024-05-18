from django.conf import settings
from django.contrib.auth.models import AbstractUser
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
from django.utils.module_loading import import_string
from rest_framework.request import Request

from .models import (
    Comment,
    CommentLike,
    CommentNotification,
    Like,
    SavedVideo,
    Video,
    VideoNotification,
)


PROFILE_QUERYSET_FACTORY = import_string(settings.PROFILE_QUERYSET_FACTORY)


def get_video_queryset(request: Request) -> BaseManager[Video]:
    queryset = (
        Video.objects.prefetch_related(
            Prefetch("profile", PROFILE_QUERYSET_FACTORY(request))
        )
        .annotate(view_count=count_related_objects_in_subquery(Video, "views"))
        .annotate(like_count=count_related_objects_in_subquery(Video, "likes"))
        .annotate(comment_count=count_related_objects_in_subquery(Video, "comments"))
    )
    queryset = annotate_videos_with_like_status(queryset, request.user)
    queryset = annotate_videos_with_saved_status(queryset, request.user)
    return queryset


def get_comment_queryset(request: Request) -> BaseManager[Comment]:
    queryset = (
        Comment.objects.prefetch_related(
            Prefetch("profile", PROFILE_QUERYSET_FACTORY(request))
        )
        .annotate(reply_count=count_related_objects_in_subquery(Comment, "replies"))
        .annotate(like_count=count_related_objects_in_subquery(Comment, "likes"))
    )
    return annotate_comments_with_like_status(queryset, request.user)


def get_videonotification_queryset(request: Request) -> BaseManager[VideoNotification]:
    return VideoNotification.objects.prefetch_related(
        Prefetch("video", get_video_queryset(request)),
        Prefetch("comment", get_comment_queryset(request)),
    )


def get_commentnotification_queryset(
    request: Request,
) -> BaseManager[CommentNotification]:
    return CommentNotification.objects.prefetch_related(
        Prefetch("video", get_video_queryset(request)),
        Prefetch("comment", get_comment_queryset(request)),
        Prefetch("reply", get_comment_queryset(request)),
    )


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

from django.contrib.auth.models import AbstractUser
from django.db.models import Model, Prefetch, QuerySet
from django.db.models.aggregates import Count
from django.db.models.expressions import Case, OuterRef, Subquery, Value, When
from django.db.models.manager import BaseManager
from rest_framework.request import Request

from .models import Profile, ProfileNotification


def get_profile_queryset(request: Request) -> BaseManager[Profile]:
    queryset = (
        Profile.objects.select_related("user")
        .annotate(
            following_count=count_related_objects_in_subquery(Profile, "following")
        )
        .annotate(
            follower_count=count_related_objects_in_subquery(Profile, "followers")
        )
    )
    queryset = annotate_profiles_with_following_status(queryset, request.user)
    return queryset


def get_profilenotification_queryset(
    request: Request,
) -> BaseManager[ProfileNotification]:
    return ProfileNotification.objects.prefetch_related(
        Prefetch("related_profile", get_profile_queryset(request)),
    )


def count_related_objects_in_subquery(model: Model, related_name: str) -> Subquery:
    """Generate a subquery to count related objects for each instance of the given model."""

    return Subquery(
        model.objects.filter(pk=OuterRef("pk"))
        .annotate(count=Count(related_name, distinct=True))
        .values("count")
    )


def annotate_profiles_with_following_status(
    queryset: QuerySet, user: AbstractUser
) -> QuerySet:
    """Annotate the given profile queryset with a field indicating whether the user is following each profile."""

    if not user.is_authenticated:
        return queryset.annotate(is_following=Value(False))

    following_ids = user.profile.following.values_list("followed_id")

    return queryset.annotate(
        is_following=Case(
            When(id__in=following_ids, then=Value(True)),
            default=Value(False),
        )
    )

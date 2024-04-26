from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, transaction
from django.db.models import Model, Prefetch, QuerySet
from django.db.models.aggregates import Count
from django.db.models.expressions import Case, OuterRef, Subquery, Value, When
from django.db.models.manager import BaseManager
from django.db.models.query import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Follow, Profile
from .pagination import FollowPagination, ProfilePagination
from .serializers import ProfileSerializer
from .utils import normalize_search_query


USER_MODEL = get_user_model()


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


class ProfileViewSet(RetrieveModelMixin, GenericViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = ProfileSerializer
    pagination_class = ProfilePagination

    def get_queryset(self):
        return get_profile_queryset(self.request)

    @transaction.atomic()
    @action(
        detail=False, methods=["GET", "PATCH"], permission_classes=[IsAuthenticated]
    )
    def me(self, request: Request):
        try:
            profile_id = request.user.profile.id
        except USER_MODEL.profile.RelatedObjectDoesNotExist:
            raise Http404("User has no profile")

        profile = self.get_queryset().get(pk=profile_id)

        if request.method == "GET":
            serializer = ProfileSerializer(profile, context={"request": self.request})
            return Response(serializer.data)
        elif request.method == "PATCH":
            serializer = ProfileSerializer(
                profile,
                data=request.data,
                partial=True,
                context={"request": self.request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="retrieve_by_username/(?P<username>.+)",
    )
    def retrieve_by_username(self, request: Request, username: str):
        profile = get_object_or_404(self.get_queryset(), user__username=username)
        serializer = ProfileSerializer(profile, context={"request": self.request})
        return Response(serializer.data)

    @action(detail=False, methods=["GET"])
    def search(self, request: Request):
        query = request.query_params.get("query", "")
        if not query.strip():
            raise ParseError("You must provide a query")

        normalized_query = normalize_search_query(query)

        profiles = self.get_queryset().filter(
            Q(user__username__icontains=normalized_query)
            | Q(full_name__icontains=normalized_query)
        )

        page = self.paginate_queryset(profiles)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
        url_path="follow/(?P<username>.+)",
    )
    def follow(self, request: Request, username: str):
        own_profile = request.user.profile
        profile = get_object_or_404(Profile, user__username=username)

        if profile.id == own_profile.id:
            raise ParseError("You cannot follow your own profile")

        try:
            Follow.objects.create(follower=own_profile, followed=profile)
        except IntegrityError:
            raise ParseError(detail="You are already following this profile")

        return Response(status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
        url_path="unfollow/(?P<username>.+)",
    )
    def unfollow(self, request: Request, username: str):
        own_profile = request.user.profile
        profile = get_object_or_404(Profile, user__username=username)

        Follow.objects.filter(follower=own_profile, followed=profile).delete()

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="following/(?P<username>.+)")
    def following(self, request: Request, username: str):
        profile = get_object_or_404(Profile, user__username=username)
        follows = Follow.objects.prefetch_related(
            Prefetch("followed", get_profile_queryset(self.request))
        ).filter(follower=profile)

        pagination = FollowPagination()
        follows = pagination.paginate_queryset(follows, self.request, view=self)

        profiles = [follow.followed for follow in follows]

        serializer = self.get_serializer(profiles, many=True)
        return pagination.get_paginated_response(serializer.data)

    @action(detail=False, methods=["GET"], url_path="followers/(?P<username>.+)")
    def followers(self, request: Request, username: str):
        profile = get_object_or_404(Profile, user__username=username)
        follows = Follow.objects.prefetch_related(
            Prefetch("follower", get_profile_queryset(self.request))
        ).filter(followed=profile)

        pagination = FollowPagination()
        follows = pagination.paginate_queryset(follows, self.request, view=self)

        profiles = [follow.follower for follow in follows]

        serializer = self.get_serializer(profiles, many=True)
        return pagination.get_paginated_response(serializer.data)

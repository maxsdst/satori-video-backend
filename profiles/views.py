from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
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
from .pagination import FollowPagination, ProfileSearchPagination
from .querysets import get_profile_queryset
from .serializers import ProfileSerializer
from .utils import normalize_search_query


USER_MODEL = get_user_model()


class ProfileViewSet(RetrieveModelMixin, GenericViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = ProfileSerializer

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

        profiles = (
            self.get_queryset()
            .filter(
                Q(user__username__icontains=normalized_query)
                | Q(full_name__icontains=normalized_query)
            )
            .order_by("-follower_count")
        )

        pagination = ProfileSearchPagination()
        page = pagination.paginate_queryset(profiles, self.request, self)
        serializer = self.get_serializer(page, many=True)
        return pagination.get_paginated_response(serializer.data)

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

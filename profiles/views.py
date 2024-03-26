from django.contrib.auth import get_user_model
from django.db.models.query import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Profile
from .pagination import ProfilePagination
from .serializers import ProfileSerializer
from .utils import normalize_search_query


USER_MODEL = get_user_model()


class ProfileViewSet(RetrieveModelMixin, GenericViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    queryset = Profile.objects.select_related("user").all()
    serializer_class = ProfileSerializer
    pagination_class = ProfilePagination

    @action(
        detail=False, methods=["GET", "PATCH"], permission_classes=[IsAuthenticated]
    )
    def me(self, request: Request):
        try:
            profile = request.user.profile
        except USER_MODEL.profile.RelatedObjectDoesNotExist:
            raise Http404("User has no profile")

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
        profile = get_object_or_404(
            Profile.objects.select_related("user"), user__username=username
        )
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

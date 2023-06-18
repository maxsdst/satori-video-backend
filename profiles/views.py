from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Profile
from .serializers import ProfileSerializer


USER_MODEL = get_user_model()


class ProfileViewSet(RetrieveModelMixin, GenericViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    queryset = Profile.objects.select_related("user").all()
    serializer_class = ProfileSerializer

    @action(
        detail=False, methods=["GET", "PATCH"], permission_classes=[IsAuthenticated]
    )
    def me(self, request: Request):
        try:
            profile = request.user.profile
        except USER_MODEL.profile.RelatedObjectDoesNotExist:
            raise Http404("User has no profile")

        if request.method == "GET":
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        elif request.method == "PATCH":
            serializer = ProfileSerializer(
                profile,
                data=request.data,
                partial=True,
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
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

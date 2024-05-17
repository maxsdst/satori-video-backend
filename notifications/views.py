from django.conf import settings
from django.db.models import Model, Prefetch
from django.utils import timezone
from django.utils.decorators import classonlymethod
from django.utils.module_loading import import_string
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Notification
from .pagination import NotificationPagination
from .permissions import UserOwnsObjectOrReadOnly
from .serializers import MarkAsSeenSerializer


def get_child_instance(parent_instance: Model, child_models: list) -> Model:
    for model in child_models:
        try:
            return getattr(parent_instance, model.__name__.lower())
        except model.DoesNotExist:
            pass
        except AttributeError:
            raise ValueError(
                f"{model.__name__} is not a child of {parent_instance.__class__.__name__}"
            )

    raise ValueError("No child instances found")


class NotificationViewSet(DestroyModelMixin, GenericViewSet):
    http_method_names = ["get", "post", "delete", "head", "options"]
    permission_classes = [IsAuthenticated, UserOwnsObjectOrReadOnly]
    pagination_class = NotificationPagination

    notification_model_config = {}

    @classonlymethod
    def as_view(cls, *args, **kwargs):
        try:
            map = settings.NOTIFICATION_MODEL_CONFIG
        except AttributeError:
            raise TypeError("NOTIFICATION_MODEL_CONFIG setting must be set")
        if not isinstance(map, dict):
            raise TypeError("NOTIFICATION_MODEL_CONFIG setting must be a dict")

        for model_path, config in map.items():
            model = import_string(model_path)
            queryset_factory = import_string(config["queryset_factory"])
            serializer = import_string(config["serializer"])
            if not issubclass(model, Notification):
                raise TypeError(
                    "Model in NOTIFICATION_MODEL_CONFIG must be a subclass of Notification model"
                )
            cls.notification_model_config[model] = {
                "queryset_factory": queryset_factory,
                "serializer": serializer,
            }

        return super().as_view(*args, **kwargs)

    def get_queryset(self):
        profile = self.request.user.profile
        queryset = Notification.objects.filter(profile_id=profile.id)

        for model, config in self.notification_model_config.items():
            factory = config["queryset_factory"]
            queryset = queryset.prefetch_related(
                Prefetch(model.__name__.lower(), factory(self.request))
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        results = []
        for item in page:
            item = get_child_instance(item, self.notification_model_config.keys())
            serializer = self.notification_model_config[item.__class__]["serializer"]
            data = serializer(item, context={"request": request}).data
            results.append(data)

        return self.get_paginated_response(results)

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def mark_as_seen(self, request: Request):
        profile = request.user.profile

        serializer = MarkAsSeenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification_ids = serializer.data["notification_ids"]

        Notification.objects.filter(profile=profile, id__in=notification_ids).update(
            is_seen=True, seen_date=timezone.now()
        )

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], permission_classes=[IsAuthenticated])
    def unseen_count(self, request):
        profile = request.user.profile
        unseen_count = Notification.objects.filter(
            profile=profile, is_seen=False
        ).count()
        return Response({"unseen_count": unseen_count})

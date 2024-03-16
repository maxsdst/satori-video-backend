import math
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.files.base import File
from django.db.models import QuerySet
from django.db.models.sql.where import WhereNode
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from .constants import (
    COMMENT_POPULARITY_TIME_DECAY_RATE,
    SECONDS_IN_DAY,
    CommentPopularityWeight,
)


def get_media_path(target: Path) -> str:
    """Get path to the file relative to MEDIA_ROOT folder."""

    relative_path = target.relative_to(settings.MEDIA_ROOT)
    return relative_path.as_posix()


def get_file_extension(file: File) -> str:
    """Get extension of the Django File."""

    return Path(file.name).suffix.upper()[1:]


def has_any_filter_applied(
    request: Request, filter_fields: list[str], viewset: ModelViewSet
) -> bool:
    "Check whether a request includes any filter based on specified fields."

    for param in get_filter_query_params(filter_fields, viewset):
        if param in request.query_params:
            return True

    return False


def get_filter_query_params(fields: list[str], viewset: ModelViewSet) -> list[str]:
    "Get filter query params for specified fields from a viewset."

    if hasattr(viewset, "filterset_class"):
        return get_filter_query_params_from_filterset_class(fields, viewset)
    elif hasattr(viewset, "filterset_fields"):
        return get_filter_query_params_from_filterset_fields(fields, viewset)
    else:
        return []


def get_filter_query_params_from_filterset_class(
    fields: list[str], viewset: ModelViewSet
):
    "Get filter query params for specified fields from filterset_class of a viewset."

    params = []

    for name, filter in viewset.filterset_class().filters.items():
        for field in fields:
            if filter.field_name == field:
                params.append(name)

    return params


def get_filter_query_params_from_filterset_fields(
    fields: list[str], viewset: ModelViewSet
):
    "Get filter query params for specified fields from filterset_fields of a viewset."

    params = []

    for field, lookups in viewset.filterset_fields.items():
        if field in fields:
            for lookup in lookups:
                param = f"{field}__{lookup}" if lookup != "exact" else field
                params.append(param)

    return params


def get_days_since_date(date: datetime) -> float:
    time_since_created = timezone.now() - date
    return time_since_created.total_seconds() / SECONDS_IN_DAY


def exponential_decay(days_since_event: float, decay_rate: float) -> float:
    return math.exp(-decay_rate * days_since_event)


def calculate_comment_popularity_score(comment) -> int:
    score = (
        comment.likes.count() * CommentPopularityWeight.LIKE
        + comment.replies.count() * CommentPopularityWeight.REPLY
    )

    decay_factor = exponential_decay(
        get_days_since_date(comment.creation_date),
        COMMENT_POPULARITY_TIME_DECAY_RATE,
    )

    return round(score * decay_factor)


def update_comment_popularity_score(comment, save: bool = True) -> None:
    comment.popularity_score = calculate_comment_popularity_score(comment)

    if save:
        comment.save()


def get_objects_by_primary_keys(queryset: QuerySet, primary_keys: list) -> list:
    """
    Get objects from the provided queryset by a list of primary keys, preserving the order of keys.
    All filters from the queryset will be removed. Non-existent primary keys will be skipped.
    """

    # remove ordering
    queryset = queryset.order_by()
    # remove filters
    queryset.query.where = WhereNode()

    objects = queryset.in_bulk(primary_keys)
    return [objects[pk] for pk in primary_keys if pk in objects]

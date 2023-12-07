from pathlib import Path

from django.conf import settings
from django.core.files.base import File
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet


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

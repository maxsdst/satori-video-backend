from django_filters import FilterSet, NumberFilter

from .models import Video


class VideoFilter(FilterSet):
    class Meta:
        model = Video
        fields = {
            "profile": ["exact"],
            "title": ["icontains"],
            "description": ["icontains"],
        }

    view_count__lte = NumberFilter(method="filter_view_count")
    view_count__gte = NumberFilter(method="filter_view_count")

    def filter_view_count(self, queryset, name, value):
        return queryset.filter(**{name: value})

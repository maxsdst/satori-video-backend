from django_filters import FilterSet, ModelChoiceFilter, NumberFilter

from .models import Comment, Video


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


class CommentFilter(FilterSet):
    class Meta:
        model = Comment
        fields = {
            "parent": ["exact"],
        }

    video = ModelChoiceFilter(queryset=Video.objects.all(), method="filter_video")

    def filter_video(self, queryset, name, value):
        return queryset.filter(parent__isnull=True, **{name: value})

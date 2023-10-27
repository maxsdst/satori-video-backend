from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework import serializers

from .models import Upload, Video


PROFILE_SERIALIZER = import_string(settings.PROFILE_SERIALIZER)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            "id",
            "profile",
            "upload_date",
            "title",
            "description",
            "source",
            "thumbnail",
            "first_frame",
        ]
        read_only_fields = [
            "profile",
            "upload_date",
            "source",
            "thumbnail",
            "first_frame",
        ]

    profile = PROFILE_SERIALIZER()


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ["id", "profile", "filename", "video", "is_done"]

    video = VideoSerializer()


class CreateUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ["id", "file"]

    def create(self, validated_data: dict):
        return Upload.objects.create(
            **validated_data,
            profile_id=self.context["profile_id"],
            filename=validated_data["file"].name
        )

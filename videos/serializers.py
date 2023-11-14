from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string
from rest_framework import serializers

from .models import Upload, Video, View
from .signals import video_updated


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
            "view_count",
        ]
        read_only_fields = [
            "profile",
            "upload_date",
            "source",
            "thumbnail",
            "first_frame",
            "view_count",
        ]

    profile = PROFILE_SERIALIZER()
    view_count = serializers.IntegerField()

    @transaction.atomic()
    def update(self, instance, validated_data):
        video = super().update(instance, validated_data)
        video_updated.send(self.__class__, video=video)
        return video


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ["id", "profile", "creation_date", "filename", "video", "is_done"]

    video = VideoSerializer()


class CreateUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ["id", "file"]

    def create(self, validated_data: dict):
        return Upload.objects.create(
            **validated_data,
            profile_id=self.context["profile_id"],
            filename=validated_data["file"].name,
        )


class CreateViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ["id", "video"]

    def create(self, validated_data: dict):
        return View.objects.create(
            **validated_data,
            profile_id=self.context["profile_id"],
            session_id=self.context["session_id"],
        )

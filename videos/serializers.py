from rest_framework import serializers

from .models import Upload, Video


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "user", "title", "description", "source", "thumbnail"]


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ["id", "user", "video"]

    video = VideoSerializer


class CreateUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ["id", "file"]

    def create(self, validated_data: dict):
        return Upload.objects.create(user_id=self.context["user_id"], **validated_data)

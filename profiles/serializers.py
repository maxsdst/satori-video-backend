from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .constants import AVATAR_FILENAME_LENGTH, AVATAR_IMAGE_QUALITY
from .models import Profile
from .utils import convert_image_to_jpg, get_available_random_filename


class CreateProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()

    class Meta:
        model = Profile
        fields = ["id", "user_id", "full_name"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "full_name",
            "description",
            "avatar",
            "following_count",
            "follower_count",
            "is_following",
        ]
        read_only_fields = [
            "id",
            "user",
            "following_count",
            "follower_count",
            "is_following",
        ]

    user = UserSerializer(read_only=True)
    following_count = serializers.IntegerField()
    follower_count = serializers.IntegerField()
    is_following = serializers.BooleanField()

    def update(self, instance, validated_data):
        if "avatar" in validated_data:
            validated_data["avatar"] = convert_image_to_jpg(
                validated_data["avatar"], quality=AVATAR_IMAGE_QUALITY
            )
            validated_data["avatar"].name = get_available_random_filename(
                settings.MEDIA_ROOT / Profile.avatar.field.upload_to,
                Path(validated_data["avatar"].name).suffix,
                AVATAR_FILENAME_LENGTH,
            )

        return super().update(instance, validated_data)

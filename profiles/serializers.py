from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Profile


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
        fields = ["id", "user", "full_name", "description", "avatar"]

    user = UserSerializer(read_only=True)

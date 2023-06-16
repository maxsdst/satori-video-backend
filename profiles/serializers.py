from rest_framework import serializers

from .models import Profile


class CreateProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()

    class Meta:
        model = Profile
        fields = ["id", "user_id", "full_name"]

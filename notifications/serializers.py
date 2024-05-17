from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "subtype",
            "profile",
            "creation_date",
            "is_seen",
        ]
        read_only_fields = [
            "id",
            "type",
            "subtype",
            "profile",
            "creation_date",
            "is_seen",
        ]


class MarkAsSeenSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(child=serializers.IntegerField())

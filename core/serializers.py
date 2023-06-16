from django.db import transaction
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer

from profiles.signals import user_created


class UserCreateSerializer(BaseUserCreateSerializer):
    @transaction.atomic()
    def create(self, validated_data):
        user = super().create(validated_data)
        user_created.send(self.__class__, user=user, request=self.context["request"])
        return user

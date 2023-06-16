from django.dispatch import receiver

from profiles.serializers import CreateProfileSerializer

from . import user_created


@receiver(user_created)
def on_user_created(sender, user, request, **kwargs):
    serializer = CreateProfileSerializer(data={**request.data, "user_id": user.id})
    serializer.is_valid(raise_exception=True)
    serializer.save()

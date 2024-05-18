from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.serializers import CreateProfileSerializer

from ..models import Follow, ProfileNotification
from . import user_created


@receiver(user_created)
def on_user_created(sender, user, request, **kwargs):
    serializer = CreateProfileSerializer(data={**request.data, "user_id": user.id})
    serializer.is_valid(raise_exception=True)
    serializer.save()


@receiver(post_save, sender=Follow)
def on_post_save_follow_notify_followed_profile(sender, instance: Follow, **kwargs):
    ProfileNotification.objects.create(
        subtype="new_follower",
        profile=instance.followed,
        related_profile=instance.follower,
    )

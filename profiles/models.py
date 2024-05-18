from django.conf import settings
from django.db import models, transaction

from notifications.models import Notification


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50)
    description = models.CharField(max_length=250, blank=True)
    avatar = models.ImageField(upload_to="avatars", null=True, blank=True)


class Follow(models.Model):
    class Meta:
        unique_together = ["follower", "followed"]
        ordering = ["-creation_date"]

    follower = models.ForeignKey(
        Profile, related_name="following", on_delete=models.CASCADE
    )
    followed = models.ForeignKey(
        Profile, related_name="followers", on_delete=models.CASCADE
    )
    creation_date = models.DateTimeField(auto_now_add=True)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class ProfileNotification(Notification):
    class Type(models.TextChoices):
        PROFILE = "profile"

    class Subtype(models.TextChoices):
        NEW_FOLLOWER = "new_follower"

    type = models.CharField(max_length=50, choices=Type.choices, default=Type.PROFILE)
    subtype = models.CharField(max_length=50, choices=Subtype.choices)
    related_profile = models.ForeignKey(Profile, null=True, on_delete=models.CASCADE)

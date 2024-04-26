from django.db import models
from django.conf import settings


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

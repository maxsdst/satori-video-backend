from django.conf import settings
from django.db import models


class Video(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="videos"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=2000)
    source = models.URLField()
    thumbnail = models.URLField()


class Upload(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploads"
    )
    file = models.FileField(upload_to="uploads")
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, null=True, related_name="+"
    )
    is_done = models.BooleanField(default=False)

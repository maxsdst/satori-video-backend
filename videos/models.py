from django.conf import settings
from django.db import models


class Video(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="videos"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=2000)
    source = models.FileField(upload_to="videos")
    thumbnail = models.ImageField(upload_to="thumbnails")

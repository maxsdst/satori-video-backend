from django.conf import settings
from django.db import models

from .validators import (
    validate_video_duration,
    validate_video_extension,
    validate_video_size,
)


class Video(models.Model):
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="videos"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=2000)
    source = models.URLField()
    thumbnail = models.URLField()


class Upload(models.Model):
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="uploads"
    )
    file = models.FileField(
        upload_to="uploads",
        validators=[
            validate_video_extension,
            validate_video_size,
            validate_video_duration,
        ],
    )
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, null=True, related_name="+"
    )
    is_done = models.BooleanField(default=False)

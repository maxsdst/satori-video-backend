from django.dispatch import receiver

from ..models import Upload, Video
from . import video_updated


@receiver(video_updated)
def on_video_updated(sender, video: Video, **kwargs):
    Upload.objects.filter(video=video).delete()

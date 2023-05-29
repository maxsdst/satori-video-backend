from pathlib import Path

from django.conf import settings


VIDEOS_FOLDER = settings.MEDIA_ROOT / "videos"
TEMP_FOLDER = Path("temp")
ALLOWED_VIDEO_EXTENSIONS = ("MP4", "MOV", "MPEG", "3GP", "AVI")

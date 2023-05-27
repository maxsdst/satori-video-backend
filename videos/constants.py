from pathlib import Path

from django.conf import settings


VIDEOS_FOLDER = settings.MEDIA_ROOT / "videos"
TEMP_FOLDER = Path("temp")

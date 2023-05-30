from pathlib import Path

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage


def get_media_url(target: Path) -> str:
    """Get URL of the file in MEDIA_ROOT folder."""

    relative_path = str(target).replace(str(settings.MEDIA_ROOT), "")
    return default_storage.url(relative_path)


def get_file_extension(file: File) -> str:
    """Get extension of the Django File."""

    return Path(file.name).suffix.upper()[1:]

from pathlib import Path

from django.conf import settings
from django.core.files.base import File


def get_media_path(target: Path) -> str:
    """Get path to the file relative to MEDIA_ROOT folder."""

    relative_path = target.relative_to(settings.MEDIA_ROOT)
    return relative_path.as_posix()


def get_file_extension(file: File) -> str:
    """Get extension of the Django File."""

    return Path(file.name).suffix.upper()[1:]

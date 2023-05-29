from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from .constants import ALLOWED_VIDEO_EXTENSIONS
from .utils import get_file_extension, get_video_duration


def validate_video_extension(file: InMemoryUploadedFile):
    extension = get_file_extension(file)
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError(
            f"Unsupported video format. Allowed formats: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )


def validate_video_size(file: InMemoryUploadedFile):
    max_size_mb = 50

    if file.size > max_size_mb * (1024**2):
        raise ValidationError(f"Video cannot be larger than {max_size_mb} MB")


def validate_video_duration(file: InMemoryUploadedFile):
    max_duration_seconds = 90

    # ignore this validator if the file is not a valid video
    extension = get_file_extension(file)
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return

    duration = get_video_duration(file.chunks())
    if duration > max_duration_seconds:
        raise ValidationError(
            f"Video cannot be longer than {max_duration_seconds} seconds"
        )

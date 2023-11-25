from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models.fields.files import FieldFile

from .constants import TEMP_FOLDER
from .models import Upload, Video
from .utils import get_media_path
from .video_processing import (
    create_thumbnail,
    create_vertical_video,
    extract_first_frame,
    make_hls,
)


@shared_task()
@transaction.atomic()
def handle_upload(upload_id: int, profile_id: int) -> None:
    VIDEOS_FOLDER = settings.MEDIA_ROOT / "videos"

    upload = Upload.objects.get(id=upload_id)

    title = Path(upload.filename).stem

    video = Video.objects.create(
        profile_id=profile_id,
        title=title,
        description="",
        source="",
        thumbnail="",
    )

    upload_path = Path(upload.file.path)
    video_path = TEMP_FOLDER / upload_path.name

    try:
        create_vertical_video(upload_path, video_path)

        output_folder = VIDEOS_FOLDER / str(video.id)

        hls_playlist_path = make_hls(video_path, output_folder)
        video.source = FieldFile(video, video.source, get_media_path(hls_playlist_path))

        thumbnail_path = create_thumbnail(video_path, output_folder)
        video.thumbnail = FieldFile(
            video, video.thumbnail, get_media_path(thumbnail_path)
        )

        first_frame_path = extract_first_frame(video_path, output_folder)
        video.first_frame = FieldFile(
            video, video.first_frame, get_media_path(first_frame_path)
        )
    finally:
        video_path.unlink(missing_ok=True)

    video.save()

    upload.video = video
    upload.is_done = True
    upload.save()

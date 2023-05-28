from pathlib import Path

from celery import shared_task
from django.db import transaction

from .constants import TEMP_FOLDER, VIDEOS_FOLDER
from .models import Upload, Video
from .utils import create_thumbnail, create_vertical_video, get_media_url, make_hls


@shared_task()
@transaction.atomic()
def handle_upload(upload_id: int, user_id: int) -> None:
    upload = Upload.objects.get(id=upload_id)

    video = Video.objects.create(
        user_id=user_id,
        title="",
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
        video.source = get_media_url(hls_playlist_path)

        thumbnail_path = create_thumbnail(video_path, output_folder)
        video.thumbnail = get_media_url(thumbnail_path)
    finally:
        video_path.unlink(missing_ok=True)

    video.save()

    upload.video = video
    upload.is_done = True
    upload.save()

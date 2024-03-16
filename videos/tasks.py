from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.fields.files import FieldFile

from gorse_client import get_gorse_client

from .constants import TEMP_FOLDER
from .models import Comment, Event, Upload, Video
from .signals import video_created
from .utils import get_media_path, update_comment_popularity_score
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
    video_created.send(handle_upload, video=video)

    upload.video = video
    upload.is_done = True
    upload.save()


@shared_task()
def update_comment_popularity_scores() -> None:
    comments = Comment.objects.all()

    for comment in comments:
        update_comment_popularity_score(comment, save=False)

    Comment.objects.bulk_update(comments, ["popularity_score"])


@shared_task
def sync_recommender_system_data() -> None:
    gorse = get_gorse_client()

    users = get_user_model().objects.all()
    gorse.insert_users(
        [
            {
                "Comment": "",
                "Labels": [],
                "Subscribe": [],
                "UserId": str(user.id),
            }
            for user in users
        ]
    )

    videos = Video.objects.all()
    gorse.insert_items(
        [
            {
                "Categories": [],
                "Comment": "",
                "IsHidden": False,
                "ItemId": str(video.id),
                "Labels": [],
                "Timestamp": video.upload_date.isoformat(),
            }
            for video in videos
        ]
    )

    events = Event.objects.all()
    gorse.insert_feedbacks(
        [
            {
                "Comment": "",
                "FeedbackType": event.type,
                "ItemId": str(event.video.id),
                "Timestamp": event.creation_date.isoformat(),
                "UserId": str(event.profile.user.id),
            }
            for event in events
        ]
    )


@shared_task
def insert_user_in_recommender_system(user_id: int) -> None:
    gorse = get_gorse_client()
    gorse.insert_user(
        {
            "Comment": "",
            "Labels": [],
            "Subscribe": [],
            "UserId": str(user_id),
        }
    )


@shared_task
def delete_user_from_recommender_system(user_id: int) -> None:
    gorse = get_gorse_client()
    gorse.delete_user(user_id)


@shared_task
def insert_video_in_recommender_system(video_id: int) -> None:
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return

    gorse = get_gorse_client()
    gorse.insert_item(
        {
            "Categories": [],
            "Comment": "",
            "IsHidden": False,
            "ItemId": str(video.id),
            "Labels": [],
            "Timestamp": video.upload_date.isoformat(),
        },
    )


@shared_task
def delete_video_from_recommender_system(video_id: int) -> None:
    gorse = get_gorse_client()
    gorse.delete_item(video_id)


@shared_task
def insert_feedback_in_recommender_system(event_id: int) -> None:
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    gorse = get_gorse_client()
    gorse.insert_feedback(
        event.type,
        str(event.profile.user.id),
        str(event.video.id),
        event.creation_date.isoformat(),
    )

    event.delete()

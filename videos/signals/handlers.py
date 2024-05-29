from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from rest_framework.request import Request

from ..models import (
    Comment,
    CommentLike,
    CommentNotification,
    Event,
    Upload,
    Video,
    VideoNotification,
)
from ..serializers import CreateHistoryEntrySerializer
from ..tasks import (
    delete_user_from_recommender_system,
    delete_video_from_recommender_system,
    insert_feedback_in_recommender_system,
    insert_user_in_recommender_system,
    insert_video_in_recommender_system,
)
from ..utils import update_comment_popularity_score
from . import video_created, video_updated, view_created


USER_MODEL = get_user_model()


@receiver(video_updated)
def on_video_updated(sender, video: Video, **kwargs):
    Upload.objects.filter(video=video).delete()


@receiver(post_save, sender=Comment)
def on_post_save_comment(sender, instance: Comment, created: bool, **kwargs):
    if created and instance.parent:
        update_comment_popularity_score(instance.parent)


@receiver(post_delete, sender=Comment)
def on_post_delete_comment(sender, instance: Comment, **kwargs):
    try:
        if instance.parent:
            update_comment_popularity_score(instance.parent)
    except Comment.DoesNotExist:
        pass


@receiver(post_save, sender=CommentLike)
def on_post_save_comment_like(sender, instance: CommentLike, created: bool, **kwargs):
    if created:
        update_comment_popularity_score(instance.comment)


@receiver(post_delete, sender=CommentLike)
def on_post_delete_comment_like(sender, instance: CommentLike, **kwargs):
    update_comment_popularity_score(instance.comment)


@receiver(post_save, sender=USER_MODEL)
def on_post_save_user_insert_into_recommender(
    sender, instance: AbstractUser, created: bool, **kwargs
):
    if created:
        insert_user_in_recommender_system.delay(instance.id)


@receiver(post_delete, sender=USER_MODEL)
def on_post_delete_user_delete_from_recommender(
    sender, instance: AbstractUser, **kwargs
):
    delete_user_from_recommender_system.delay(instance.id)


@receiver(video_created)
def on_video_created_insert_into_recommender(sender, video: Video, **kwargs):
    insert_video_in_recommender_system.delay(video.id)


@receiver(post_delete, sender=Video)
def on_post_delete_video_delete_from_recommender(sender, instance: Video, **kwargs):
    delete_video_from_recommender_system.delay(instance.id)


@receiver(post_save, sender=Event)
def on_post_save_event_insert_into_recommender(
    sender, instance: Event, created: bool, **kwargs
):
    if created:
        insert_feedback_in_recommender_system.delay(instance.id)


@receiver(view_created)
def on_view_created_create_history_entry(sender, request: Request, **kwargs):
    if not request.user.is_authenticated:
        return

    serializer = CreateHistoryEntrySerializer(
        data=request.data, context={"profile_id": request.user.profile.id}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()


@receiver(video_created)
def on_video_created_notify_owner_upload_processed(sender, video: Video, **kwargs):
    VideoNotification.objects.create(
        subtype="upload_processed",
        profile=video.profile,
        video=video,
    )


@receiver(video_created)
def on_video_created_notify_followers(sender, video: Video, **kwargs):
    with transaction.atomic():
        for follow in video.profile.followers.all():
            VideoNotification.objects.create(
                subtype="followed_profile_video", profile=follow.follower, video=video
            )


@receiver(post_save, sender=Comment)
def on_post_save_comment_notify_video_owner(
    sender, instance: Comment, created: bool, **kwargs
):
    if not created:
        return
    if instance.profile.id == instance.video.profile.id:
        return
    if instance.parent:
        return

    VideoNotification.objects.create(
        subtype="comment",
        profile=instance.video.profile,
        video=instance.video,
        comment=instance,
    )


@receiver(post_save, sender=Comment)
def on_post_save_comment_notify_user_of_reply(
    sender, instance: Comment, created: bool, **kwargs
):
    if not created:
        return
    if instance.parent is None:
        return

    profile = (
        instance.mentioned_profile
        if instance.mentioned_profile
        else instance.parent.profile
    )

    if profile.id == instance.profile.id:
        return

    CommentNotification.objects.create(
        subtype="reply",
        profile=profile,
        video=instance.video,
        comment=instance.parent,
        reply=instance,
    )


@receiver(post_save, sender=CommentLike)
def on_post_save_comment_like_notify_comment_owner(
    sender, instance: CommentLike, created: bool, **kwargs
):
    if not created:
        return
    if instance.profile == instance.comment.profile:
        return

    CommentNotification.objects.create(
        subtype="like",
        profile=instance.comment.profile,
        video=instance.comment.video,
        comment=instance.comment,
    )

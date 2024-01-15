from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..models import Comment, CommentLike, Upload, Video
from ..utils import update_comment_popularity_score
from . import video_updated


@receiver(video_updated)
def on_video_updated(sender, video: Video, **kwargs):
    Upload.objects.filter(video=video).delete()


@receiver(post_save, sender=Comment)
def on_post_save_comment(sender, instance: Comment, created: bool, **kwargs):
    if created and instance.parent:
        update_comment_popularity_score(instance.parent)


@receiver(post_delete, sender=Comment)
def on_post_delete_comment(sender, instance: Comment, **kwargs):
    if instance.parent:
        update_comment_popularity_score(instance.parent)


@receiver(post_save, sender=CommentLike)
def on_post_save_comment_like(sender, instance: CommentLike, created: bool, **kwargs):
    if created:
        update_comment_popularity_score(instance.comment)


@receiver(post_delete, sender=CommentLike)
def on_post_delete_comment_like(sender, instance: CommentLike, **kwargs):
    update_comment_popularity_score(instance.comment)

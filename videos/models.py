from django.conf import settings
from django.db import models, transaction

from notifications.models import Notification

from .validators import (
    validate_video_duration,
    validate_video_extension,
    validate_video_size,
)


class Video(models.Model):
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="videos"
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=2000, blank=True)
    source = models.FileField()
    thumbnail = models.FileField()
    first_frame = models.FileField()

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    @transaction.atomic()
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)


class Upload(models.Model):
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="uploads"
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(
        upload_to="uploads",
        validators=[
            validate_video_extension,
            validate_video_size,
            validate_video_duration,
        ],
    )
    filename = models.CharField(max_length=100)
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, null=True, related_name="+"
    )
    is_done = models.BooleanField(default=False)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class View(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="views")
    profile = models.ForeignKey(
        settings.PROFILE_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="views",
    )
    session_id = models.UUIDField()
    creation_date = models.DateTimeField(auto_now_add=True)


class HistoryEntry(models.Model):
    class Meta:
        ordering = ["-creation_date"]

    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="history_entries"
    )
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="history"
    )
    creation_date = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
    class Meta:
        unique_together = ["video", "profile"]

    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="likes")
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="video_likes"
    )
    creation_date = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    class Reason(models.TextChoices):
        SEX = "sex", "Sexual content"
        VIOLENCE = "violence", "Violent or repulsive content"
        HATE = "hate", "Hateful or abusive content"
        HARASSMENT = "harassment", "Harassment or bullying"
        DANGER = "danger", "Harmful or dangerous acts"
        MISINFORMATION = "misinformation", "Misinformation"
        CHILD_ABUSE = "child_abuse", "Child abuse"
        TERRORISM = "terrorism", "Promotes terrorism"
        SPAM = "spam", "Spam or misleading"

    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="reports")
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="video_reports"
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)


class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="comments")
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    parent = models.ForeignKey(
        "self", null=True, on_delete=models.CASCADE, related_name="replies"
    )
    mentioned_profile = models.ForeignKey(
        settings.PROFILE_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="mentioned_in_comments",
    )
    mentioned_profile_username = models.CharField(max_length=250, null=True)
    text = models.TextField(max_length=2000)
    creation_date = models.DateTimeField(auto_now_add=True)
    popularity_score = models.IntegerField(default=0)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class CommentLike(models.Model):
    class Meta:
        unique_together = ["comment", "profile"]

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="comment_likes"
    )

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class CommentReport(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", "Unwanted commercial content or spam"
        PORNOGRAPHY = "pornography", "Pornography or sexually explicit material"
        CHILD_ABUSE = "child_abuse", "Child abuse"
        HATE_SPEECH = "hate_speech", "Hate speech or graphic violence"
        TERRORISM = "terrorism", "Promotes terrorism"
        HARASSMENT = "harassment", "Harassment or bullying"
        SUICIDE = "suicide", "Suicide or self injury"
        MISINFORMATION = "misinformation", "Misinformation"

    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="reports"
    )
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="comment_reports"
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)


class SavedVideo(models.Model):
    class Meta:
        unique_together = ["video", "profile"]
        ordering = ["-creation_date"]

    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="saved_videos"
    )
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="saved_videos"
    )
    creation_date = models.DateTimeField(auto_now_add=True)


class Event(models.Model):
    class Type(models.TextChoices):
        VIEW = "view"
        LIKE = "like"
        SHARE = "share"
        SAVE = "save"

    type = models.CharField(max_length=20, choices=Type.choices)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="events")
    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="events"
    )
    creation_date = models.DateTimeField(auto_now_add=True)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class VideoNotification(Notification):
    class Type(models.TextChoices):
        VIDEO = "video"

    class Subtype(models.TextChoices):
        UPLOAD_PROCESSED = "upload_processed"
        COMMENT = "comment"
        FOLLOWED_PROFILE_VIDEO = "followed_profile_video"

    type = models.CharField(max_length=50, choices=Type.choices, default=Type.VIDEO)
    subtype = models.CharField(max_length=50, choices=Subtype.choices)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, null=True, on_delete=models.CASCADE)


class CommentNotification(Notification):
    class Type(models.TextChoices):
        COMMENT = "comment"

    class Subtype(models.TextChoices):
        LIKE = "like"
        REPLY = "reply"

    type = models.CharField(max_length=50, choices=Type.choices, default=Type.COMMENT)
    subtype = models.CharField(max_length=50, choices=Subtype.choices)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    comment = models.ForeignKey(
        Comment,
        null=True,
        on_delete=models.CASCADE,
        related_name="notifications_comment",
    )
    reply = models.ForeignKey(
        Comment, null=True, on_delete=models.CASCADE, related_name="notifications_reply"
    )

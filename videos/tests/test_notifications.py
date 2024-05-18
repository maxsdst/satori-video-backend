import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework import status

from videos.models import Comment, CommentNotification, VideoNotification


LIST_VIEWNAME = "notifications:notifications-list"


@pytest.fixture
def list_notifications(list_objects):
    def _list_notifications(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_notifications


@pytest.mark.django_db
class TestListNotifications:
    def test_returns_video_notifications(
        self, authenticate, user, list_notifications, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment)
        notification = baker.make(VideoNotification, profile=profile, comment=comment)

        response = list_notifications()

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": notification.id,
            "type": notification.type,
            "subtype": notification.subtype,
            "profile": notification.profile.id,
            "creation_date": isoformat(notification.creation_date),
            "is_seen": notification.is_seen,
            "video": {
                "id": notification.video.id,
                "profile": {
                    "id": notification.video.profile.id,
                    "user": {
                        "id": notification.video.profile.user.id,
                        "username": notification.video.profile.user.username,
                    },
                    "full_name": notification.video.profile.full_name,
                    "description": notification.video.profile.description,
                    "avatar": notification.video.profile.avatar,
                    "following_count": 0,
                    "follower_count": 0,
                    "is_following": False,
                },
                "upload_date": isoformat(notification.video.upload_date),
                "title": notification.video.title,
                "description": notification.video.description,
                "source": (
                    notification.video.source.url if notification.video.source else None
                ),
                "thumbnail": (
                    notification.video.thumbnail.url
                    if notification.video.thumbnail
                    else None
                ),
                "first_frame": (
                    notification.video.first_frame.url
                    if notification.video.first_frame
                    else None
                ),
                "view_count": 0,
                "like_count": 0,
                "is_liked": False,
                "comment_count": 0,
                "is_saved": False,
            },
            "comment": {
                "id": notification.comment.id,
                "video": notification.comment.video.id,
                "profile": {
                    "id": notification.comment.profile.id,
                    "user": {
                        "id": notification.comment.profile.user.id,
                        "username": notification.comment.profile.user.username,
                    },
                    "full_name": notification.comment.profile.full_name,
                    "description": notification.comment.profile.description,
                    "avatar": notification.comment.profile.avatar,
                    "following_count": 0,
                    "follower_count": 0,
                    "is_following": False,
                },
                "parent": (
                    notification.comment.parent.id
                    if notification.comment.parent
                    else notification.comment.parent
                ),
                "mentioned_profile": None,
                "mentioned_profile_username": None,
                "text": notification.comment.text,
                "creation_date": isoformat(notification.comment.creation_date),
                "reply_count": 0,
                "like_count": 0,
                "is_liked": False,
                "popularity_score": 0,
            },
        }

    def test_returns_comment_notifications(
        self, authenticate, user, list_notifications, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment)
        reply = baker.make(Comment)
        notification = baker.make(
            CommentNotification, profile=profile, comment=comment, reply=reply
        )

        response = list_notifications()

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": notification.id,
            "type": notification.type,
            "subtype": notification.subtype,
            "profile": notification.profile.id,
            "creation_date": isoformat(notification.creation_date),
            "is_seen": notification.is_seen,
            "video": {
                "id": notification.video.id,
                "profile": {
                    "id": notification.video.profile.id,
                    "user": {
                        "id": notification.video.profile.user.id,
                        "username": notification.video.profile.user.username,
                    },
                    "full_name": notification.video.profile.full_name,
                    "description": notification.video.profile.description,
                    "avatar": notification.video.profile.avatar,
                    "following_count": 0,
                    "follower_count": 0,
                    "is_following": False,
                },
                "upload_date": isoformat(notification.video.upload_date),
                "title": notification.video.title,
                "description": notification.video.description,
                "source": (
                    notification.video.source.url if notification.video.source else None
                ),
                "thumbnail": (
                    notification.video.thumbnail.url
                    if notification.video.thumbnail
                    else None
                ),
                "first_frame": (
                    notification.video.first_frame.url
                    if notification.video.first_frame
                    else None
                ),
                "view_count": 0,
                "like_count": 0,
                "is_liked": False,
                "comment_count": 0,
                "is_saved": False,
            },
            "comment": {
                "id": notification.comment.id,
                "video": notification.comment.video.id,
                "profile": {
                    "id": notification.comment.profile.id,
                    "user": {
                        "id": notification.comment.profile.user.id,
                        "username": notification.comment.profile.user.username,
                    },
                    "full_name": notification.comment.profile.full_name,
                    "description": notification.comment.profile.description,
                    "avatar": notification.comment.profile.avatar,
                    "following_count": 0,
                    "follower_count": 0,
                    "is_following": False,
                },
                "parent": (
                    notification.comment.parent.id
                    if notification.comment.parent
                    else notification.comment.parent
                ),
                "mentioned_profile": None,
                "mentioned_profile_username": None,
                "text": notification.comment.text,
                "creation_date": isoformat(notification.comment.creation_date),
                "reply_count": 0,
                "like_count": 0,
                "is_liked": False,
                "popularity_score": 0,
            },
            "reply": {
                "id": notification.reply.id,
                "video": notification.reply.video.id,
                "profile": {
                    "id": notification.reply.profile.id,
                    "user": {
                        "id": notification.reply.profile.user.id,
                        "username": notification.reply.profile.user.username,
                    },
                    "full_name": notification.reply.profile.full_name,
                    "description": notification.reply.profile.description,
                    "avatar": notification.reply.profile.avatar,
                    "following_count": 0,
                    "follower_count": 0,
                    "is_following": False,
                },
                "parent": (
                    notification.reply.parent.id
                    if notification.reply.parent
                    else notification.reply.parent
                ),
                "mentioned_profile": None,
                "mentioned_profile_username": None,
                "text": notification.reply.text,
                "creation_date": isoformat(notification.reply.creation_date),
                "reply_count": 0,
                "like_count": 0,
                "is_liked": False,
                "popularity_score": 0,
            },
        }

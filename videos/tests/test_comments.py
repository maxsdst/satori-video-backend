from datetime import timedelta
from time import sleep

import pytest
from django.conf import settings
from django.utils import timezone
from model_bakery import baker
from rest_framework import status

from videos.constants import CommentPopularityWeight
from videos.models import Comment, CommentLike, Video
from videos.tasks import update_comment_popularity_scores
from videos.utils import update_comment_popularity_score


LIST_VIEWNAME = "videos:comments-list"
DETAIL_VIEWNAME = "videos:comments-detail"


@pytest.fixture
def create_comment(create_object):
    def _create_comment(comment):
        return create_object(LIST_VIEWNAME, comment, format="json")

    return _create_comment


@pytest.fixture
def retrieve_comment(retrieve_object):
    def _retrieve_comment(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_comment


@pytest.fixture
def update_comment(update_object):
    def _update_comment(pk, comment):
        return update_object(DETAIL_VIEWNAME, pk, comment)

    return _update_comment


@pytest.fixture
def delete_comment(delete_object):
    def _delete_comment(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_comment


@pytest.fixture
def list_comments(list_objects):
    def _list_comments(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_comments


@pytest.mark.django_db
class TestCreateComment:
    def test_if_user_is_anonymous_returns_401(self, create_comment):
        response = create_comment({})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, create_comment):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_comment(
            {"video": 1, "parent": 1, "text": "", "mentioned_profile": 123}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None
        assert response.data["parent"] is not None
        assert response.data["text"] is not None
        assert response.data["mentioned_profile"] is not None

    def test_if_data_is_valid_returns_201(self, authenticate, user, create_comment):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = create_comment(
            {"video": video.id, "parent": None, "text": "a", "mentioned_profile": None}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0

    def test_can_create_reply(self, authenticate, user, create_comment):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)
        comment = baker.make(Comment, video=video)

        response = create_comment(
            {
                "video": video.id,
                "parent": comment.id,
                "text": "a",
                "mentioned_profile": None,
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0

    def test_cannot_create_reply_with_wrong_video(
        self, authenticate, user, create_comment
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video1 = baker.make(Video)
        video2 = baker.make(Video)
        comment = baker.make(Comment, video=video1)

        response = create_comment(
            {
                "video": video2.id,
                "parent": comment.id,
                "text": "a",
                "mentioned_profile": None,
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] is not None

    def test_cannot_create_reply_to_reply(self, authenticate, user, create_comment):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)
        comment = baker.make(Comment, video=video)
        reply = baker.make(Comment, video=video, parent=comment)

        response = create_comment(
            {
                "video": video.id,
                "parent": reply.id,
                "text": "a",
                "mentioned_profile": None,
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] is not None

    def test_derives_mentioned_profile_username_from_mentioned_profile(
        self, authenticate, user, other_user, create_comment
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        video = baker.make(Video)
        parent = baker.make(Comment, video=video)

        response = create_comment(
            {
                "video": video.id,
                "parent": parent.id,
                "text": "a",
                "mentioned_profile": other_profile.id,
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0
        assert response.data["mentioned_profile"] == other_profile.id
        assert (
            response.data["mentioned_profile_username"] == other_profile.user.username
        )

    def test_cannot_mention_profile_in_top_level_comment(
        self, authenticate, user, other_user, create_comment
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        video = baker.make(Video)

        response = create_comment(
            {
                "video": video.id,
                "parent": None,
                "text": "a",
                "mentioned_profile": other_profile.id,
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] is not None


@pytest.mark.django_db
class TestRetrieveComment:
    def test_if_comment_doesnt_exist_returns_404(self, retrieve_comment):
        response = retrieve_comment(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_comment_exists_returns_200(self, retrieve_comment, isoformat):
        comment = baker.make(Comment)

        response = retrieve_comment(comment.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": comment.id,
            "video": comment.video.id,
            "profile": {
                "id": comment.profile.id,
                "user": {
                    "id": comment.profile.user.id,
                    "username": comment.profile.user.username,
                },
                "full_name": comment.profile.full_name,
                "description": comment.profile.description,
                "avatar": comment.profile.avatar,
                "following_count": 0,
                "follower_count": 0,
                "is_following": False,
            },
            "parent": comment.parent.id if comment.parent else comment.parent,
            "mentioned_profile": None,
            "mentioned_profile_username": None,
            "text": comment.text,
            "creation_date": isoformat(comment.creation_date),
            "reply_count": 0,
            "like_count": 0,
            "is_liked": False,
            "popularity_score": 0,
        }

    def test_reply_count(self, retrieve_comment):
        comment = baker.make(Comment)
        baker.make(Comment, parent=comment, _quantity=2)

        response = retrieve_comment(comment.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == comment.id
        assert response.data["reply_count"] == 2

    def test_is_liked_field(self, authenticate, user, retrieve_comment):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment1 = baker.make(Comment)
        comment2 = baker.make(Comment)
        baker.make(CommentLike, comment=comment2, profile=profile)

        response1 = retrieve_comment(comment1.id)
        response2 = retrieve_comment(comment2.id)

        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["is_liked"] == False
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["is_liked"] == True

    def test_like_count(self, retrieve_comment):
        comment = baker.make(Comment)
        baker.make(CommentLike, comment=comment, _quantity=2)

        response = retrieve_comment(comment.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == comment.id
        assert response.data["like_count"] == 2


@pytest.mark.django_db
class TestUpdateComment:
    def test_if_user_is_anonymous_returns_401(self, update_comment):
        response = update_comment(1, {})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_comment_doesnt_exist_returns_404(
        self, authenticate, user, update_comment
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = update_comment(1, {})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_doesnt_own_comment_returns_403(
        self, authenticate, user, other_user, update_comment
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        comment = baker.make(Comment, profile=other_profile)

        response = update_comment(comment.id, {})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_change_video(self, authenticate, user, update_comment):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video1 = baker.make(Video)
        video2 = baker.make(Video)
        comment = baker.make(Comment, profile=profile, video=video1)

        response = update_comment(comment.id, {"video": video2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["video"] == video1.id

    def test_cannot_change_profile(
        self, authenticate, user, other_user, update_comment
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        comment = baker.make(Comment, profile=profile)

        response = update_comment(comment.id, {"profile": other_profile.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["id"] == profile.id

    def test_cannot_change_parent(self, authenticate, user, update_comment):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)
        parent1 = baker.make(Comment, video=video, parent=None)
        parent2 = baker.make(Comment, video=video, parent=None)
        comment = baker.make(Comment, profile=profile, video=video, parent=parent1)

        response = update_comment(comment.id, {"parent": parent2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["parent"] == parent1.id

    def test_cannot_change_creation_date(
        self, authenticate, user, update_comment, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment, profile=profile)
        new_creation_date = isoformat(timezone.now() - timedelta(days=1))

        response = update_comment(comment.id, {"creation_date": new_creation_date})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["creation_date"] == isoformat(comment.creation_date)

    def test_if_data_is_invalid_returns_400(self, authenticate, user, update_comment):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment, profile=profile)

        response = update_comment(comment.id, {"text": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["text"] is not None

    def test_if_data_is_valid_returns_200(self, authenticate, user, update_comment):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment, profile=profile)
        new_text = "a"

        response = update_comment(comment.id, {"text": new_text})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["text"] == new_text


@pytest.mark.django_db
class TestDeleteComment:
    def test_if_user_is_anonymous_returns_401(self, delete_comment):
        response = delete_comment(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_comment_doesnt_exist_returns_404(
        self, authenticate, user, delete_comment
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = delete_comment(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_doesnt_own_comment_returns_403(
        self, authenticate, user, other_user, delete_comment
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        comment = baker.make(Comment, profile=other_profile)

        response = delete_comment(comment.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_user_owns_comment_returns_204(self, authenticate, user, delete_comment):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment, profile=profile)

        response = delete_comment(comment.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_deletes_comment_with_replies(self, authenticate, user, delete_comment):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        comment = baker.make(Comment, profile=profile)
        baker.make(Comment, parent=comment)
        baker.make(Comment, parent=comment)
        initial_count = Comment.objects.count()

        response = delete_comment(comment.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert initial_count == 3
        assert Comment.objects.count() == 0


@pytest.mark.django_db
class TestListComments:
    def test_if_no_filter_applied_returns_403(self, list_comments):
        response = list_comments()

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_video_filter_applied_returns_200(
        self, list_comments, filter, isoformat
    ):
        video = baker.make(Video)
        comment = baker.make(Comment, video=video)

        response = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)]
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0] == {
            "id": comment.id,
            "video": comment.video.id,
            "profile": {
                "id": comment.profile.id,
                "user": {
                    "id": comment.profile.user.id,
                    "username": comment.profile.user.username,
                },
                "full_name": comment.profile.full_name,
                "description": comment.profile.description,
                "avatar": comment.profile.avatar,
                "following_count": 0,
                "follower_count": 0,
                "is_following": False,
            },
            "parent": comment.parent.id if comment.parent else comment.parent,
            "mentioned_profile": None,
            "mentioned_profile_username": None,
            "text": comment.text,
            "creation_date": isoformat(comment.creation_date),
            "reply_count": 0,
            "like_count": 0,
            "is_liked": False,
            "popularity_score": 0,
        }

    def test_if_parent_filter_applied_returns_200(
        self, list_comments, filter, isoformat
    ):
        video = baker.make(Video)
        parent = baker.make(Comment, video=video)
        comment = baker.make(Comment, video=video, parent=parent)

        response = list_comments(
            filters=[filter(field="parent", lookup_type="exact", value=parent.id)]
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0] == {
            "id": comment.id,
            "video": comment.video.id,
            "profile": {
                "id": comment.profile.id,
                "user": {
                    "id": comment.profile.user.id,
                    "username": comment.profile.user.username,
                },
                "full_name": comment.profile.full_name,
                "description": comment.profile.description,
                "avatar": comment.profile.avatar,
                "following_count": 0,
                "follower_count": 0,
                "is_following": False,
            },
            "parent": comment.parent.id if comment.parent else comment.parent,
            "mentioned_profile": None,
            "mentioned_profile_username": None,
            "text": comment.text,
            "creation_date": isoformat(comment.creation_date),
            "reply_count": 0,
            "like_count": 0,
            "is_liked": False,
            "popularity_score": 0,
        }

    def test_if_video_filter_applied_doesnt_include_replies(
        self, list_comments, filter
    ):
        video = baker.make(Video)
        comment = baker.make(Comment, video=video)
        reply = baker.make(Comment, video=video, parent=comment)

        response = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)]
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == comment.id

    def test_if_video_and_parent_filters_applied_returns_replies(
        self, list_comments, filter
    ):
        video = baker.make(Video)
        parent = baker.make(Comment, video=video)
        reply = baker.make(Comment, video=video, parent=parent)

        response = list_comments(
            filters=[
                filter(field="video", lookup_type="exact", value=video.id),
                filter(field="parent", lookup_type="exact", value=parent.id),
            ]
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == reply.id

    def test_filtering_by_video(self, list_comments, filter):
        video1 = baker.make(Video)
        video2 = baker.make(Video)
        comment1 = baker.make(Comment, video=video1)
        comment2 = baker.make(Comment, video=video1)
        comment3 = baker.make(Comment, video=video2)

        response = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video1.id)]
        )

        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == comment1.id
        assert response.data["results"][1]["id"] == comment2.id

    def test_filtering_by_parent(self, list_comments, filter):
        video = baker.make(Video)
        parent1 = baker.make(Comment, video=video)
        parent2 = baker.make(Comment, video=video)
        comment1 = baker.make(Comment, video=video, parent=parent1)
        comment2 = baker.make(Comment, video=video, parent=parent1)
        comment3 = baker.make(Comment, video=video, parent=parent2)

        response = list_comments(
            filters=[filter(field="parent", lookup_type="exact", value=parent1.id)]
        )

        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == comment1.id
        assert response.data["results"][1]["id"] == comment2.id

    def test_ordering_by_creation_date(self, list_comments, filter, ordering):
        video = baker.make(Video)
        comment1 = baker.make(Comment, video=video)
        sleep(0.0001)
        comment2 = baker.make(Comment, video=video)
        sleep(0.0001)
        comment3 = baker.make(Comment, video=video)

        response1 = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            ordering=ordering(field="creation_date", direction="ASC"),
        )
        response2 = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            ordering=ordering(field="creation_date", direction="DESC"),
        )

        assert response1.data["results"][0]["id"] == comment1.id
        assert response1.data["results"][1]["id"] == comment2.id
        assert response1.data["results"][2]["id"] == comment3.id
        assert response2.data["results"][0]["id"] == comment3.id
        assert response2.data["results"][1]["id"] == comment2.id
        assert response2.data["results"][2]["id"] == comment1.id

    def test_ordering_by_popularity_score(self, list_comments, filter, ordering):
        video = baker.make(Video)
        comment1 = baker.make(Comment, video=video, popularity_score=20)
        comment2 = baker.make(Comment, video=video, popularity_score=0)
        comment3 = baker.make(Comment, video=video, popularity_score=10)

        response1 = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            ordering=ordering(field="popularity_score", direction="ASC"),
        )
        response2 = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            ordering=ordering(field="popularity_score", direction="DESC"),
        )

        assert response1.data["results"][0]["id"] == comment2.id
        assert response1.data["results"][1]["id"] == comment3.id
        assert response1.data["results"][2]["id"] == comment1.id
        assert response2.data["results"][0]["id"] == comment1.id
        assert response2.data["results"][1]["id"] == comment3.id
        assert response2.data["results"][2]["id"] == comment2.id

    def test_snapshot_pagination(self, list_comments, filter, pagination, api_client):
        video = baker.make(Video)
        comments = [baker.make(Comment, video=video) for i in range(3)]

        response1 = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            pagination=pagination(type="cursor", page_size=2),
        )
        response2 = api_client.get(response1.data["next"])

        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == comments[0].id
        assert response1.data["results"][1]["id"] == comments[1].id
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == comments[2].id

    def test_order_is_stable(
        self, list_comments, filter, ordering, pagination, api_client
    ):
        video = baker.make(Video)
        items = [
            baker.make(Comment, video=video, popularity_score=i + 1) for i in range(5)
        ]
        items[3].popularity_score = 1000
        items[3].save()
        initial_order = list(
            Comment.objects.order_by("popularity_score").values_list("id", flat=True)
        )

        response1 = list_comments(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            ordering=ordering(field="popularity_score", direction="ASC"),
            pagination=pagination(type="cursor", page_size=2),
        )
        items[1].popularity_score = 100
        items[4].popularity_score = 0
        Comment.objects.bulk_update(items, ["popularity_score"])
        order = list(
            Comment.objects.order_by("popularity_score").values_list("id", flat=True)
        )
        response2 = api_client.get(response1.data["next"])
        response3 = api_client.get(response2.data["next"])

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_200_OK
        assert order != initial_order
        assert [
            response1.data["results"][0]["id"],
            response1.data["results"][1]["id"],
            response2.data["results"][0]["id"],
            response2.data["results"][1]["id"],
            response3.data["results"][0]["id"],
        ] == initial_order


@pytest.mark.django_db
class TestPopularityScore:
    def test_score_is_initially_0(self):
        comment = baker.make(Comment)

        assert comment.popularity_score == 0

    def test_likes_increase_score(self):
        comment = baker.make(Comment)
        like_count = 3

        baker.make(CommentLike, comment=comment, _quantity=like_count)
        comment.refresh_from_db()

        assert comment.popularity_score == like_count * CommentPopularityWeight.LIKE

    def test_replies_increase_score(self):
        comment = baker.make(Comment)
        reply_count = 3

        baker.make(Comment, parent=comment, _quantity=reply_count)
        comment.refresh_from_db()

        assert comment.popularity_score == reply_count * CommentPopularityWeight.REPLY

    def test_deleting_like_decreases_score(self):
        comment = baker.make(Comment)
        baker.make(CommentLike, comment=comment, _quantity=2)
        like = baker.make(CommentLike, comment=comment)
        comment.refresh_from_db()
        initial_score = comment.popularity_score

        like.delete()
        comment.refresh_from_db()

        assert initial_score - comment.popularity_score == CommentPopularityWeight.LIKE

    def test_deleting_reply_decreases_score(self):
        comment = baker.make(Comment)
        baker.make(Comment, parent=comment, _quantity=2)
        reply = baker.make(Comment, parent=comment)
        comment.refresh_from_db()
        initial_score = comment.popularity_score

        reply.delete()
        comment.refresh_from_db()

        assert initial_score - comment.popularity_score == CommentPopularityWeight.REPLY

    def test_time_decay(self):
        comment1 = baker.make(Comment)
        comment2 = baker.make(Comment)
        comment3 = baker.make(Comment)
        like_count = 30
        baker.make(CommentLike, comment=comment1, _quantity=like_count)
        baker.make(CommentLike, comment=comment2, _quantity=like_count)
        baker.make(CommentLike, comment=comment3, _quantity=like_count)

        comment2.creation_date = timezone.now() - timedelta(days=100)
        comment3.creation_date = timezone.now() - timedelta(days=200)
        update_comment_popularity_score(comment2, save=False)
        update_comment_popularity_score(comment3, save=False)

        assert (
            comment1.popularity_score
            > comment2.popularity_score
            > comment3.popularity_score
        )

    def test_periodic_task_updates_score(self):
        comment1 = baker.make(Comment)
        comment2 = baker.make(Comment)
        baker.make(CommentLike, comment=comment1, _bulk_create=True, _quantity=2)
        baker.make(CommentLike, comment=comment2, _bulk_create=True, _quantity=2)
        comment1.refresh_from_db()
        comment2.refresh_from_db()
        comment1_initial_score = comment1.popularity_score
        comment2_initial_score = comment2.popularity_score

        update_comment_popularity_scores.apply()
        comment1.refresh_from_db()
        comment2.refresh_from_db()

        assert comment1_initial_score == 0
        assert comment1.popularity_score > 0
        assert comment2_initial_score == 0
        assert comment2.popularity_score > 0

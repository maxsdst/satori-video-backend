from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from model_bakery import baker

from videos.models import Event, Video
from videos.tasks import (
    delete_user_from_recommender_system,
    delete_video_from_recommender_system,
    insert_feedback_in_recommender_system,
    insert_user_in_recommender_system,
    insert_video_in_recommender_system,
    sync_recommender_system_data,
)


USER_MODEL = get_user_model()


def are_datetimes_approximately_equal(datetime1: datetime, datetime2: datetime):
    return datetime1 - datetime2 < timedelta(seconds=1)


def is_video_correctly_inserted_in_gorse(video: Video, item: dict):
    return int(item["ItemId"]) == video.id and are_datetimes_approximately_equal(
        video.upload_date, datetime.fromisoformat(item["Timestamp"])
    )


def is_feedback_correctly_inserted_in_gorse(event: Event, feedback: dict):
    return (
        feedback["FeedbackType"] == event.type
        and int(feedback["ItemId"]) == event.video.id
        and int(feedback["UserId"]) == event.profile.user.id
        and are_datetimes_approximately_equal(
            event.creation_date, datetime.fromisoformat(feedback["Timestamp"])
        )
    )


@pytest.mark.django_db
@pytest.mark.recommender
class TestSyncRecommenderSystemData:
    def test_inserts_users(self, gorse):
        baker.make(USER_MODEL, _quantity=3, _bulk_create=True)
        user_objects = USER_MODEL.objects.all()
        initial_users, _ = gorse.get_users(n=10)

        sync_recommender_system_data.apply()
        users, _ = gorse.get_users(n=10)

        assert len(initial_users) == 0
        assert len(users) == 3
        for user_obj in user_objects:
            assert (
                len([user for user in users if user["UserId"] == str(user_obj.id)]) == 1
            )

    def test_inserts_videos(self, gorse):
        baker.make(Video, _quantity=3, _bulk_create=True)
        videos = Video.objects.all()
        initial_items, _ = gorse.get_items(n=10)

        sync_recommender_system_data.apply()
        items, _ = gorse.get_items(n=10)

        assert len(initial_items) == 0
        assert len(items) == 3
        for video in videos:
            for item in items:
                if int(item["ItemId"]) == video.id:
                    assert is_video_correctly_inserted_in_gorse(video, item)
                    break
            else:
                assert False

    def test_inserts_feedbacks(self, gorse):
        profile = baker.make(settings.PROFILE_MODEL)
        baker.make(Event, profile=profile, _quantity=3, _bulk_create=True)
        events = Event.objects.all()
        initial_feedbacks = gorse.list_feedbacks("", profile.user.id)

        sync_recommender_system_data.apply()
        feedbacks = gorse.list_feedbacks("", profile.user.id)

        assert len(initial_feedbacks) == 0
        assert len(feedbacks) == 3
        for event in events:
            for feedback in feedbacks:
                if int(feedback["ItemId"]) == event.video.id:
                    assert is_feedback_correctly_inserted_in_gorse(event, feedback)
                    break
            else:
                assert False


@pytest.mark.django_db
@pytest.mark.recommender
class TestInsertUserInRecommenderSystem:
    def test_inserts_user(self, gorse):
        user_id = 123
        initial_users, _ = gorse.get_users(n=10)

        insert_user_in_recommender_system.apply([user_id])
        users, _ = gorse.get_users(n=10)

        assert len(initial_users) == 0
        assert len(users) == 1
        assert int(users[0]["UserId"]) == user_id


@pytest.mark.django_db
@pytest.mark.recommender
class TestDeleteUserFromRecommenderSystem:
    def test_deletes_user(self, gorse):
        user_id = 123
        gorse.insert_user(
            {
                "Comment": "",
                "Labels": [],
                "Subscribe": [],
                "UserId": str(user_id),
            }
        )
        initial_users, _ = gorse.get_users(n=10)

        delete_user_from_recommender_system.apply([user_id])
        users, _ = gorse.get_users(n=10)

        assert len(initial_users) == 1
        assert int(initial_users[0]["UserId"]) == user_id
        assert len(users) == 0


@pytest.mark.django_db
@pytest.mark.recommender
class TestInsertVideoInRecommenderSystem:
    def test_inserts_video(self, gorse):
        baker.make(Video, _quantity=2, _bulk_create=True)
        video = Video.objects.all()[0]
        initial_items, _ = gorse.get_items(n=10)

        insert_video_in_recommender_system.apply([video.id])
        items, _ = gorse.get_items(n=10)

        assert len(initial_items) == 0
        assert len(items) == 1
        assert is_video_correctly_inserted_in_gorse(video, items[0])


@pytest.mark.django_db
@pytest.mark.recommender
class TestDeleteVideoFromRecommenderSystem:
    def test_deletes_video(self, gorse):
        video_id = 123
        gorse.insert_item(
            {
                "Categories": [],
                "Comment": "",
                "IsHidden": False,
                "ItemId": str(video_id),
                "Labels": [],
                "Timestamp": "2020-02-02T20:20:02Z",
            },
        )
        initial_items, _ = gorse.get_items(n=10)

        delete_video_from_recommender_system.apply([video_id])
        items, _ = gorse.get_items(n=10)

        assert len(initial_items) == 1
        assert int(initial_items[0]["ItemId"]) == video_id
        assert len(items) == 0


@pytest.mark.django_db
@pytest.mark.recommender
class TestInsertFeedbackInRecommenderSystem:
    def test_inserts_feedback(self, gorse):
        profile = baker.make(settings.PROFILE_MODEL)
        baker.make(Event, profile=profile, _quantity=2, _bulk_create=True)
        event = Event.objects.all()[1]
        initial_feedbacks = gorse.list_feedbacks("", profile.user.id)

        insert_feedback_in_recommender_system.apply([event.id])
        feedbacks = gorse.list_feedbacks("", profile.user.id)

        assert len(initial_feedbacks) == 0
        assert len(feedbacks) == 1
        assert is_feedback_correctly_inserted_in_gorse(event, feedbacks[0])

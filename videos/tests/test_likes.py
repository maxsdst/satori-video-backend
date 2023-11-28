from time import sleep

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from videos.models import Like, Video


LIST_VIEWNAME = "videos:likes-list"
DETAIL_VIEWNAME = "videos:likes-detail"


@pytest.fixture
def create_like(create_object):
    def _create_like(like):
        return create_object(LIST_VIEWNAME, like)

    return _create_like


@pytest.fixture
def retrieve_like(retrieve_object):
    def _retrieve_like(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_like


@pytest.fixture
def update_like(update_object):
    def _update_like(pk, like):
        return update_object(DETAIL_VIEWNAME, pk, like)

    return _update_like


@pytest.fixture
def delete_like(delete_object):
    def _delete_like(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_like


@pytest.fixture
def list_likes(list_objects):
    def _list_likes(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_likes


@pytest.fixture
def remove_like(api_client):
    def _remove_like(video_id):
        return api_client.post(reverse("videos:likes-remove-like"), {"video": video_id})

    return _remove_like


@pytest.mark.django_db
class TestCreateLike:
    def test_if_user_is_anonymous_returns_401(self, create_like):
        response = create_like({"video": 1})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, create_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_like({"video": 123})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None

    def test_if_data_is_valid_returns_201(self, authenticate, user, create_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = create_like({"video": video.id})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0

    def test_cannot_create_duplicate_like(self, authenticate, user, create_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response1 = create_like({"video": video.id})
        response2 = create_like({"video": video.id})

        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.data["id"] > 0
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.data["detail"] is not None


@pytest.mark.django_db
class TestRetrieveLike:
    def test_if_like_doesnt_exist_returns_404(self, retrieve_like):
        response = retrieve_like(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_like_exists_returns_200(self, user, retrieve_like, isoformat):
        like = baker.make(Like)

        response = retrieve_like(like.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": like.id,
            "profile": {
                "id": like.profile.id,
                "user": {
                    "id": like.profile.user.id,
                    "username": like.profile.user.username,
                },
                "full_name": like.profile.full_name,
                "description": like.profile.description,
                "avatar": like.profile.avatar,
            },
            "video": {
                "id": like.video.id,
                "profile": {
                    "id": like.video.profile.id,
                    "user": {
                        "id": like.video.profile.user.id,
                        "username": like.video.profile.user.username,
                    },
                    "full_name": like.video.profile.full_name,
                    "description": like.video.profile.description,
                    "avatar": like.video.profile.avatar,
                },
                "upload_date": isoformat(like.video.upload_date),
                "title": like.video.title,
                "description": like.video.description,
                "source": like.video.source.url if like.video.source else None,
                "thumbnail": like.video.thumbnail.url if like.video.thumbnail else None,
                "first_frame": like.video.first_frame.url
                if like.video.first_frame
                else None,
                "view_count": 0,
                "like_count": 1,
            },
            "creation_date": isoformat(like.creation_date),
        }


@pytest.mark.django_db
class TestUpdateLike:
    def test_returns_405(self, authenticate, user, update_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = update_like(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteLike:
    def test_returns_405(self, authenticate, user, delete_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = delete_like(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListLikes:
    def test_if_no_filter_applied_returns_403(self, list_likes):
        response = list_likes()

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_video_or_profile_filter_applied_returns_200(
        self, list_likes, filter, isoformat
    ):
        profile = baker.make(settings.PROFILE_MODEL)
        video = baker.make(Video)
        like = baker.make(Like, video=video, profile=profile)

        response1 = list_likes(
            filters=[filter(field="video", lookup_type="exact", value=video.id)]
        )
        response2 = list_likes(
            filters=[filter(field="profile", lookup_type="exact", value=profile.id)]
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["count"] == 1
        assert response1.data["results"][0] == {
            "id": like.id,
            "profile": {
                "id": like.profile.id,
                "user": {
                    "id": like.profile.user.id,
                    "username": like.profile.user.username,
                },
                "full_name": like.profile.full_name,
                "description": like.profile.description,
                "avatar": like.profile.avatar,
            },
            "video": {
                "id": video.id,
                "profile": {
                    "id": video.profile.id,
                    "user": {
                        "id": video.profile.user.id,
                        "username": video.profile.user.username,
                    },
                    "full_name": video.profile.full_name,
                    "description": video.profile.description,
                    "avatar": video.profile.avatar,
                },
                "upload_date": isoformat(video.upload_date),
                "title": video.title,
                "description": video.description,
                "source": video.source.url if video.source else None,
                "thumbnail": video.thumbnail.url if video.thumbnail else None,
                "first_frame": video.first_frame.url if video.first_frame else None,
                "view_count": 0,
                "like_count": 1,
            },
            "creation_date": isoformat(like.creation_date),
        }
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["count"] == 1
        assert response2.data["results"][0]["id"] == like.id

    def test_filtering_by_video(self, list_likes, filter):
        video1 = baker.make(Video)
        video2 = baker.make(Video)
        like1 = baker.make(Like, video=video1)
        like2 = baker.make(Like, video=video1)
        like3 = baker.make(Like, video=video2)

        response = list_likes(
            filters=[filter(field="video", lookup_type="exact", value=video1.id)]
        )

        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == like1.id
        assert response.data["results"][1]["id"] == like2.id

    def test_filtering_by_profile(self, list_likes, filter):
        profile1 = baker.make(settings.PROFILE_MODEL)
        profile2 = baker.make(settings.PROFILE_MODEL)
        like1 = baker.make(Like, profile=profile1)
        like2 = baker.make(Like, profile=profile1)
        like3 = baker.make(Like, profile=profile2)

        response = list_likes(
            filters=[filter(field="profile", lookup_type="exact", value=profile1.id)]
        )

        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == like1.id
        assert response.data["results"][1]["id"] == like2.id

    def test_ordering_by_creation_date(self, list_likes, filter, ordering):
        video = baker.make(Video)
        like1 = baker.make(Like, video=video)
        sleep(0.0001)
        like2 = baker.make(Like, video=video)
        sleep(0.0001)
        like3 = baker.make(Like, video=video)

        response1 = list_likes(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            ordering=ordering(field="creation_date", direction="ASC"),
        )
        response2 = list_likes(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            ordering=ordering(field="creation_date", direction="DESC"),
        )

        assert response1.data["results"][0]["id"] == like1.id
        assert response1.data["results"][1]["id"] == like2.id
        assert response1.data["results"][2]["id"] == like3.id
        assert response2.data["results"][0]["id"] == like3.id
        assert response2.data["results"][1]["id"] == like2.id
        assert response2.data["results"][2]["id"] == like1.id

    def test_limit_offset_pagination(self, list_likes, filter, pagination):
        video = baker.make(Video)
        likes = [baker.make(Like, video=video) for i in range(3)]

        response1 = list_likes(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            pagination=pagination(limit=2),
        )
        response2 = list_likes(
            filters=[filter(field="video", lookup_type="exact", value=video.id)],
            pagination=pagination(limit=2, offset=2),
        )

        assert response1.data["count"] == 3
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == likes[0].id
        assert response1.data["results"][1]["id"] == likes[1].id
        assert response2.data["count"] == 3
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == likes[2].id


@pytest.mark.django_db
class TestRemoveLike:
    def test_if_user_is_anonymous_returns_401(self, remove_like):
        response = remove_like(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, remove_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_like("a")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None

    def test_if_video_doesnt_exist_returns_400(self, authenticate, user, remove_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_like(1)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_like_doesnt_exist_returns_200(self, authenticate, user, remove_like):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = remove_like(video.id)

        assert response.status_code == status.HTTP_200_OK

    def test_deletes_like(self, authenticate, user, retrieve_like, remove_like):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)
        like = baker.make(Like, video=video, profile=profile)

        response1 = retrieve_like(like.id)
        response2 = remove_like(video.id)
        response3 = retrieve_like(like.id)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_404_NOT_FOUND

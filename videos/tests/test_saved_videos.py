from time import sleep

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from videos.models import SavedVideo, Video


LIST_VIEWNAME = "videos:saved_videos-list"
DETAIL_VIEWNAME = "videos:saved_videos-detail"


@pytest.fixture
def create_saved_video(create_object):
    def _create_saved_video(saved_video):
        return create_object(LIST_VIEWNAME, saved_video)

    return _create_saved_video


@pytest.fixture
def retrieve_saved_video(retrieve_object):
    def _retrieve_saved_video(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_saved_video


@pytest.fixture
def update_saved_video(update_object):
    def _update_saved_video(pk, saved_video):
        return update_object(DETAIL_VIEWNAME, pk, saved_video)

    return _update_saved_video


@pytest.fixture
def delete_saved_video(delete_object):
    def _delete_saved_video(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_saved_video


@pytest.fixture
def list_saved_videos(list_objects):
    def _list_saved_videos(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_saved_videos


@pytest.fixture
def remove_video_from_saved(api_client):
    def _remove_video_from_saved(video_id):
        return api_client.post(
            reverse("videos:saved_videos-remove-video-from-saved"), {"video": video_id}
        )

    return _remove_video_from_saved


@pytest.mark.django_db
class TestCreateSavedVideo:
    def test_if_user_is_anonymous_returns_401(self, create_saved_video):
        response = create_saved_video({"video": 1})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(
        self, authenticate, user, create_saved_video
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_saved_video({"video": 123})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None

    def test_if_data_is_valid_returns_201(self, authenticate, user, create_saved_video):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = create_saved_video({"video": video.id})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0

    def test_cannot_create_duplicate_saved_video(
        self, authenticate, user, create_saved_video
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response1 = create_saved_video({"video": video.id})
        response2 = create_saved_video({"video": video.id})

        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.data["id"] > 0
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.data["detail"] is not None


@pytest.mark.django_db
class TestRetrieveSavedVideo:
    def test_if_user_is_anonymous_returns_401(self, retrieve_saved_video):
        response = retrieve_saved_video({"video": 1})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_saved_video_doesnt_exist_returns_404(
        self, authenticate, user, retrieve_saved_video
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = retrieve_saved_video(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_saved_video_exists_and_user_doesnt_own_saved_video_returns_404(
        self, retrieve_saved_video, authenticate, user, other_user
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        saved_video = baker.make(SavedVideo, profile=other_profile)

        response = retrieve_saved_video(saved_video.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_saved_video_exists_and_user_owns_saved_video_returns_200(
        self, authenticate, user, retrieve_saved_video, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        saved_video = baker.make(SavedVideo, profile=profile)

        response = retrieve_saved_video(saved_video.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": saved_video.id,
            "profile": profile.id,
            "video": {
                "id": saved_video.video.id,
                "profile": {
                    "id": saved_video.video.profile.id,
                    "user": {
                        "id": saved_video.video.profile.user.id,
                        "username": saved_video.video.profile.user.username,
                    },
                    "full_name": saved_video.video.profile.full_name,
                    "description": saved_video.video.profile.description,
                    "avatar": saved_video.video.profile.avatar,
                },
                "upload_date": isoformat(saved_video.video.upload_date),
                "title": saved_video.video.title,
                "description": saved_video.video.description,
                "source": (
                    saved_video.video.source.url if saved_video.video.source else None
                ),
                "thumbnail": (
                    saved_video.video.thumbnail.url
                    if saved_video.video.thumbnail
                    else None
                ),
                "first_frame": (
                    saved_video.video.first_frame.url
                    if saved_video.video.first_frame
                    else None
                ),
                "view_count": 0,
                "like_count": 0,
                "is_liked": False,
                "comment_count": 0,
            },
            "creation_date": isoformat(saved_video.creation_date),
        }


@pytest.mark.django_db
class TestUpdateSavedVideo:
    def test_returns_405(self, authenticate, user, update_saved_video):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = update_saved_video(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteSavedVideo:
    def test_returns_405(self, authenticate, user, delete_saved_video):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = delete_saved_video(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListSavedVideos:
    def test_if_user_is_anonymous_returns_401(self, list_saved_videos):
        response = list_saved_videos()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_authenticated_returns_200(
        self, authenticate, user, list_saved_videos, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        saved_video = baker.make(SavedVideo, profile=profile)

        response = list_saved_videos()

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": saved_video.id,
            "profile": profile.id,
            "video": {
                "id": saved_video.video.id,
                "profile": {
                    "id": saved_video.video.profile.id,
                    "user": {
                        "id": saved_video.video.profile.user.id,
                        "username": saved_video.video.profile.user.username,
                    },
                    "full_name": saved_video.video.profile.full_name,
                    "description": saved_video.video.profile.description,
                    "avatar": saved_video.video.profile.avatar,
                },
                "upload_date": isoformat(saved_video.video.upload_date),
                "title": saved_video.video.title,
                "description": saved_video.video.description,
                "source": (
                    saved_video.video.source.url if saved_video.video.source else None
                ),
                "thumbnail": (
                    saved_video.video.thumbnail.url
                    if saved_video.video.thumbnail
                    else None
                ),
                "first_frame": (
                    saved_video.video.first_frame.url
                    if saved_video.video.first_frame
                    else None
                ),
                "view_count": 0,
                "like_count": 0,
                "is_liked": False,
                "comment_count": 0,
            },
            "creation_date": isoformat(saved_video.creation_date),
        }

    def test_user_can_only_get_own_saved_videos(
        self, authenticate, user, other_user, list_saved_videos
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        saved_video1 = baker.make(SavedVideo, profile=profile)
        saved_video2 = baker.make(SavedVideo, profile=other_profile)

        response = list_saved_videos()

        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == saved_video1.id

    def test_ordering_by_creation_date(
        self, authenticate, user, list_saved_videos, ordering
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        saved_video1 = baker.make(SavedVideo, profile=profile)
        sleep(0.0001)
        saved_video2 = baker.make(SavedVideo, profile=profile)
        sleep(0.0001)
        saved_video3 = baker.make(SavedVideo, profile=profile)

        response1 = list_saved_videos(
            ordering=ordering(field="creation_date", direction="ASC")
        )
        response2 = list_saved_videos(
            ordering=ordering(field="creation_date", direction="DESC")
        )

        assert response1.data["results"][0]["id"] == saved_video1.id
        assert response1.data["results"][1]["id"] == saved_video2.id
        assert response1.data["results"][2]["id"] == saved_video3.id
        assert response2.data["results"][0]["id"] == saved_video3.id
        assert response2.data["results"][1]["id"] == saved_video2.id
        assert response2.data["results"][2]["id"] == saved_video1.id

    def test_limit_offset_pagination(
        self, authenticate, user, list_saved_videos, pagination
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        saved_videos = [baker.make(SavedVideo, profile=profile) for i in range(3)]

        response1 = list_saved_videos(
            pagination=pagination(type="limit_offset", limit=2)
        )
        response2 = list_saved_videos(
            pagination=pagination(type="limit_offset", limit=2, offset=2)
        )

        assert response1.data["count"] == 3
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == saved_videos[0].id
        assert response1.data["results"][1]["id"] == saved_videos[1].id
        assert response2.data["count"] == 3
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == saved_videos[2].id


@pytest.mark.django_db
class TestRemoveVideoFromSaved:
    def test_if_user_is_anonymous_returns_401(self, remove_video_from_saved):
        response = remove_video_from_saved(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(
        self, authenticate, user, remove_video_from_saved
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_video_from_saved("a")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None

    def test_if_video_doesnt_exist_returns_400(
        self, authenticate, user, remove_video_from_saved
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_video_from_saved(1)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_saved_video_doesnt_exist_returns_200(
        self, authenticate, user, remove_video_from_saved
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = remove_video_from_saved(video.id)

        assert response.status_code == status.HTTP_200_OK

    def test_deletes_saved_video(
        self, authenticate, user, retrieve_saved_video, remove_video_from_saved
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)
        saved_video = baker.make(SavedVideo, video=video, profile=profile)

        response1 = retrieve_saved_video(saved_video.id)
        response2 = remove_video_from_saved(video.id)
        response3 = retrieve_saved_video(saved_video.id)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_404_NOT_FOUND

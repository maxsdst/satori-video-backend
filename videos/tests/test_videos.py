from datetime import timedelta
from time import sleep

import pytest
from django.conf import settings
from django.utils import timezone
from model_bakery import baker
from rest_framework import status

from videos.models import Like, Video, View


LIST_VIEWNAME = "videos:videos-list"
DETAIL_VIEWNAME = "videos:videos-detail"


@pytest.fixture
def create_video(create_object):
    def _create_video(video):
        return create_object(LIST_VIEWNAME, video)

    return _create_video


@pytest.fixture
def retrieve_video(retrieve_object):
    def _retrieve_video(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_video


@pytest.fixture
def update_video(update_object):
    def _update_video(pk, video):
        return update_object(DETAIL_VIEWNAME, pk, video, format="multipart")

    return _update_video


@pytest.fixture
def delete_video(delete_object):
    def _delete_video(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_video


@pytest.fixture
def list_videos(list_objects):
    def _list_videos(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_videos


@pytest.mark.django_db
class TestCreateVideo:
    def test_returns_405(self, create_video):
        response = create_video({})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestRetrieveVideo:
    def test_if_video_doesnt_exist_returns_404(self, retrieve_video):
        response = retrieve_video(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_video_exists_returns_200(self, retrieve_video, isoformat):
        video = baker.make(Video)

        response = retrieve_video(video.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
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
            "like_count": 0,
        }

    def test_view_count(self, retrieve_video):
        video = baker.make(Video)
        baker.make(View, video=video, _quantity=2)

        response = retrieve_video(video.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == video.id
        assert response.data["view_count"] == 2

    def test_like_count(self, retrieve_video):
        video = baker.make(Video)
        baker.make(Like, video=video, _quantity=2)

        response = retrieve_video(video.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == video.id
        assert response.data["like_count"] == 2


@pytest.mark.django_db
class TestUpdateVideo:
    def test_if_video_doesnt_exist_returns_404(self, update_video):
        response = update_video(1, {})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_is_anonymous_returns_401(self, update_video):
        video = baker.make(Video)

        response = update_video(video.id, {})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_doesnt_own_video_returns_403(
        self, authenticate, user, other_user, update_video
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        video = baker.make(Video, profile=other_profile)

        response = update_video(video.id, {})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_change_profile(self, authenticate, user, other_user, update_video):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        video = baker.make(Video, profile=profile)

        response = update_video(video.id, {"profile": other_profile.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["id"] == profile.id

    def test_cannot_change_upload_date(
        self, authenticate, user, update_video, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video, profile=profile)
        new_upload_date = isoformat(timezone.now() - timedelta(days=1))

        response = update_video(video.id, {"upload_date": new_upload_date})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["upload_date"] == isoformat(video.upload_date)

    def test_cannot_change_source(
        self, authenticate, user, update_video, generate_blank_image
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video, profile=profile)
        new_source = generate_blank_image(width=100, height=100, format="PNG")

        response = update_video(video.id, {"source": new_source})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["source"] == (video.source.url if video.source else None)

    def test_cannot_change_thumbnail(
        self, authenticate, user, update_video, generate_blank_image
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video, profile=profile)
        new_thumbnail = generate_blank_image(width=100, height=100, format="PNG")

        response = update_video(video.id, {"thumbnail": new_thumbnail})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["thumbnail"] == (
            video.thumbnail.url if video.thumbnail else None
        )

    def test_cannot_change_first_frame(
        self, authenticate, user, update_video, generate_blank_image
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video, profile=profile)
        new_first_frame = generate_blank_image(width=100, height=100, format="PNG")

        response = update_video(video.id, {"first_frame": new_first_frame})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_frame"] == (
            video.first_frame.url if video.first_frame else None
        )

    def test_if_data_is_invalid_returns_400(self, authenticate, user, update_video):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video, profile=profile)

        response = update_video(video.id, {"title": "", "description": "a" * 2100})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["title"] is not None
        assert response.data["description"] is not None

    def test_if_data_is_valid_returns_200(self, authenticate, user, update_video):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video, profile=profile)
        new_title = "a"
        new_description = "b"

        response = update_video(
            video.id, {"title": new_title, "description": new_description}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == new_title
        assert response.data["description"] == new_description


@pytest.mark.django_db
class TestDeleteVideo:
    def test_if_user_is_anonymous_returns_401(self, delete_video):
        video = baker.make(Video)

        response = delete_video(video.id)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_video_doesnt_exist_returns_404(self, authenticate, user, delete_video):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = delete_video(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_doesnt_own_video_returns_403(
        self, authenticate, user, other_user, delete_video
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        video = baker.make(Video, profile=other_profile)

        response = delete_video(video.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_user_owns_video_returns_204(self, authenticate, user, delete_video):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video, profile=profile)

        response = delete_video(video.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestListVideos:
    def test_returns_200(self, list_videos, isoformat):
        video = baker.make(Video)

        response = list_videos()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0] == {
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
            "like_count": 0,
        }

    def test_filtering_by_profile(self, list_videos, filter):
        profile1 = baker.make(settings.PROFILE_MODEL)
        profile2 = baker.make(settings.PROFILE_MODEL)
        video1 = baker.make(Video, profile=profile1)
        video2 = baker.make(Video, profile=profile1)
        video3 = baker.make(Video, profile=profile2)

        response = list_videos(
            filters=[filter(field="profile", lookup_type="exact", value=profile1.id)]
        )

        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == video1.id
        assert response.data["results"][1]["id"] == video2.id

    def test_filtering_by_title(self, list_videos, filter):
        value = "test"
        video1 = baker.make(Video, title=f"{value}1")
        video2 = baker.make(Video, title=f"{value}2")
        video3 = baker.make(Video, title="abc")

        response = list_videos(
            filters=[filter(field="title", lookup_type="icontains", value=value)]
        )

        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == video1.id
        assert response.data["results"][1]["id"] == video2.id

    def test_filtering_by_description(self, list_videos, filter):
        value = "test"
        video1 = baker.make(Video, description=f"{value}1")
        video2 = baker.make(Video, description=f"{value}2")
        video3 = baker.make(Video, description="abc")

        response = list_videos(
            filters=[filter(field="description", lookup_type="icontains", value=value)]
        )

        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == video1.id
        assert response.data["results"][1]["id"] == video2.id

    def test_ordering_by_title(self, list_videos, ordering):
        video1 = baker.make(Video, title="c")
        video2 = baker.make(Video, title="a")
        video3 = baker.make(Video, title="b")

        response1 = list_videos(ordering=ordering(field="title", direction="ASC"))
        response2 = list_videos(ordering=ordering(field="title", direction="DESC"))

        assert response1.data["results"][0]["id"] == video2.id
        assert response1.data["results"][1]["id"] == video3.id
        assert response1.data["results"][2]["id"] == video1.id
        assert response2.data["results"][0]["id"] == video1.id
        assert response2.data["results"][1]["id"] == video3.id
        assert response2.data["results"][2]["id"] == video2.id

    def test_ordering_by_upload_date(self, list_videos, ordering):
        video1 = baker.make(Video)
        sleep(0.0001)
        video2 = baker.make(Video)
        sleep(0.0001)
        video3 = baker.make(Video)

        response1 = list_videos(ordering=ordering(field="upload_date", direction="ASC"))
        response2 = list_videos(
            ordering=ordering(field="upload_date", direction="DESC")
        )

        assert response1.data["results"][0]["id"] == video1.id
        assert response1.data["results"][1]["id"] == video2.id
        assert response1.data["results"][2]["id"] == video3.id
        assert response2.data["results"][0]["id"] == video3.id
        assert response2.data["results"][1]["id"] == video2.id
        assert response2.data["results"][2]["id"] == video1.id

    def test_ordering_by_view_count(self, list_videos, ordering):
        video1 = baker.make(Video)
        video2 = baker.make(Video)
        for i in range(3):
            baker.make(View, video=video2)
        video3 = baker.make(Video)
        for i in range(2):
            baker.make(View, video=video3)

        response1 = list_videos(ordering=ordering(field="view_count", direction="ASC"))
        response2 = list_videos(ordering=ordering(field="view_count", direction="DESC"))

        assert response1.data["results"][0]["id"] == video1.id
        assert response1.data["results"][1]["id"] == video3.id
        assert response1.data["results"][2]["id"] == video2.id
        assert response2.data["results"][0]["id"] == video2.id
        assert response2.data["results"][1]["id"] == video3.id
        assert response2.data["results"][2]["id"] == video1.id

    def test_ordering_by_like_count(self, list_videos, ordering):
        video1 = baker.make(Video)
        video2 = baker.make(Video)
        for i in range(3):
            baker.make(Like, video=video2)
        video3 = baker.make(Video)
        for i in range(2):
            baker.make(Like, video=video3)

        response1 = list_videos(ordering=ordering(field="like_count", direction="ASC"))
        response2 = list_videos(ordering=ordering(field="like_count", direction="DESC"))

        assert response1.data["results"][0]["id"] == video1.id
        assert response1.data["results"][1]["id"] == video3.id
        assert response1.data["results"][2]["id"] == video2.id
        assert response2.data["results"][0]["id"] == video2.id
        assert response2.data["results"][1]["id"] == video3.id
        assert response2.data["results"][2]["id"] == video1.id

    def test_limit_offset_pagination(self, list_videos, pagination):
        videos = [baker.make(Video) for i in range(3)]

        response1 = list_videos(pagination=pagination(limit=2))
        response2 = list_videos(pagination=pagination(limit=2, offset=2))

        assert response1.data["count"] == 3
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == videos[0].id
        assert response1.data["results"][1]["id"] == videos[1].id
        assert response2.data["count"] == 3
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == videos[2].id

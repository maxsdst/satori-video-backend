from time import sleep
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework import status

from videos.models import HistoryEntry, Video


HISTORY_ENDPOINT = reverse("videos:api-root") + "history/"


@pytest.fixture
def create_history_entry(api_client):
    def _create_history_entry(history_entry):
        return api_client.post(HISTORY_ENDPOINT, history_entry)

    return _create_history_entry


@pytest.fixture
def retrieve_history_entry(api_client):
    def _retrieve_history_entry(pk):
        return api_client.get(f"{HISTORY_ENDPOINT}{pk}/")

    return _retrieve_history_entry


@pytest.fixture
def update_history_entry(api_client):
    def _update_history_entry(pk, history_entry):
        return api_client.patch(f"{HISTORY_ENDPOINT}{pk}/", history_entry)

    return _update_history_entry


@pytest.fixture
def delete_history_entry(api_client):
    def _delete_history_entry(pk):
        return api_client.delete(f"{HISTORY_ENDPOINT}{pk}/")

    return _delete_history_entry


@pytest.fixture
def list_history_entries(api_client):
    def _list_history_entries():
        return api_client.get(HISTORY_ENDPOINT)

    return _list_history_entries


@pytest.fixture
def grouped_by_date(list_objects):
    def _grouped_by_date(tz=None, *, pagination=None):
        query = {"tz": tz} if tz is not None else None
        return list_objects(
            "videos:history-grouped-by-date", query, pagination=pagination
        )

    return _grouped_by_date


@pytest.fixture
def remove_video_from_history(api_client):
    def _remove_video_from_history(video_id):
        return api_client.post(
            reverse("videos:history-remove-video-from-history"), {"video": video_id}
        )

    return _remove_video_from_history


@pytest.mark.django_db
class TestCreateHistoryEntry:
    def test_returns_404(self, authenticate, user, create_history_entry):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_history_entry({})

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRetrieveHistoryEntry:
    def test_returns_404(self, authenticate, user, retrieve_history_entry):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = retrieve_history_entry(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUpdateHistoryEntry:
    def test_returns_404(self, authenticate, user, update_history_entry):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = update_history_entry(1, {})

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestDeleteHistoryEntry:
    def test_returns_404(self, authenticate, user, delete_history_entry):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = delete_history_entry(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestListHistoryEntries:
    def test_returns_404(self, authenticate, user, list_history_entries):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = list_history_entries()

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestGroupedByDate:
    def test_if_user_is_anonymous_returns_401(self, grouped_by_date):
        response = grouped_by_date()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_timezone_is_not_provided_returns_400(
        self, authenticate, user, grouped_by_date
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = grouped_by_date()

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] is not None

    def test_if_timezone_is_invalid_returns_400(
        self, authenticate, user, grouped_by_date
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = grouped_by_date("abc")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] is not None

    def test_returns_200(self, authenticate, user, grouped_by_date, isoformat):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        entry = baker.make(HistoryEntry, profile=profile)
        tz = "Europe/Amsterdam"
        tzinfo = ZoneInfo(tz)

        response = grouped_by_date(tz)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "date": entry.creation_date.astimezone(tzinfo).date(),
            "entries": [
                {
                    "id": entry.id,
                    "profile": profile.id,
                    "video": {
                        "id": entry.video.id,
                        "profile": {
                            "id": entry.video.profile.id,
                            "user": {
                                "id": entry.video.profile.user.id,
                                "username": entry.video.profile.user.username,
                            },
                            "full_name": entry.video.profile.full_name,
                            "description": entry.video.profile.description,
                            "avatar": entry.video.profile.avatar,
                            "following_count": 0,
                            "follower_count": 0,
                            "is_following": False,
                        },
                        "upload_date": isoformat(
                            entry.video.upload_date.astimezone(tzinfo)
                        ),
                        "title": entry.video.title,
                        "description": entry.video.description,
                        "source": (
                            entry.video.source.url if entry.video.source else None
                        ),
                        "thumbnail": (
                            entry.video.thumbnail.url if entry.video.thumbnail else None
                        ),
                        "first_frame": (
                            entry.video.first_frame.url
                            if entry.video.first_frame
                            else None
                        ),
                        "view_count": 0,
                        "like_count": 0,
                        "is_liked": False,
                        "comment_count": 0,
                        "is_saved": False,
                    },
                    "creation_date": isoformat(entry.creation_date.astimezone(tzinfo)),
                }
            ],
        }

    def test_user_can_only_get_own_entries(
        self, authenticate, user, other_user, grouped_by_date
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        entry1 = baker.make(HistoryEntry, profile=profile)
        entry2 = baker.make(HistoryEntry, profile=other_profile)

        response = grouped_by_date("Europe/Amsterdam")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["entries"][0]["id"] == entry1.id

    def test_entries_ordered_by_creation_date(
        self, authenticate, user, grouped_by_date
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        entry1 = baker.make(HistoryEntry, profile=profile)
        sleep(0.0001)
        entry2 = baker.make(HistoryEntry, profile=profile)
        sleep(0.0001)
        entry3 = baker.make(HistoryEntry, profile=profile)

        response = grouped_by_date("Europe/Amsterdam")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["entries"][0]["id"] == entry3.id
        assert response.data["results"][0]["entries"][1]["id"] == entry2.id
        assert response.data["results"][0]["entries"][2]["id"] == entry1.id

    def test_is_grouped_by_date(
        self, authenticate, user, grouped_by_date, mock_current_datetime
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        tz = "Europe/Amsterdam"
        tzinfo = ZoneInfo(tz)
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 6, tzinfo=tzinfo)):
            entry1 = baker.make(HistoryEntry, profile=profile)
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 12, tzinfo=tzinfo)):
            entry2 = baker.make(HistoryEntry, profile=profile)
        with mock_current_datetime(timezone.datetime(2024, 1, 2, 6, tzinfo=tzinfo)):
            entry3 = baker.make(HistoryEntry, profile=profile)
        with mock_current_datetime(timezone.datetime(2024, 1, 4, 18, tzinfo=tzinfo)):
            entry4 = baker.make(HistoryEntry, profile=profile)

        response = grouped_by_date("Europe/Amsterdam")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["date"] == entry4.creation_date.date()
        assert len(response.data["results"][0]["entries"]) == 1
        assert response.data["results"][0]["entries"][0]["id"] == entry4.id
        assert response.data["results"][1]["date"] == entry3.creation_date.date()
        assert len(response.data["results"][1]["entries"]) == 1
        assert response.data["results"][1]["entries"][0]["id"] == entry3.id
        assert response.data["results"][2]["date"] == entry2.creation_date.date()
        assert len(response.data["results"][2]["entries"]) == 2
        assert response.data["results"][2]["entries"][0]["id"] == entry2.id
        assert response.data["results"][2]["entries"][1]["id"] == entry1.id

    def test_dates_are_timezone_aware(
        self, authenticate, user, grouped_by_date, mock_current_datetime
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        tz = "Europe/Amsterdam"
        tzinfo = ZoneInfo(tz)
        tzinfo_utc = ZoneInfo("UTC")
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 6, tzinfo=tzinfo_utc)):
            entry1 = baker.make(HistoryEntry, profile=profile)
        with mock_current_datetime(
            timezone.datetime(2024, 1, 1, 23, 55, tzinfo=tzinfo_utc)
        ):
            entry2 = baker.make(HistoryEntry, profile=profile)

        response = grouped_by_date(tz)

        assert response.status_code == status.HTTP_200_OK
        assert (
            entry1.creation_date.astimezone(tzinfo).date()
            != entry2.creation_date.astimezone(tzinfo).date()
        )
        assert len(response.data["results"]) == 2
        assert (
            response.data["results"][0]["date"]
            == entry2.creation_date.astimezone(tzinfo).date()
        )
        assert len(response.data["results"][0]["entries"]) == 1
        assert response.data["results"][0]["entries"][0]["id"] == entry2.id
        assert (
            response.data["results"][1]["date"]
            == entry1.creation_date.astimezone(tzinfo).date()
        )
        assert len(response.data["results"][1]["entries"]) == 1
        assert response.data["results"][1]["entries"][0]["id"] == entry1.id

    def test_only_latest_entry_per_video_per_date_is_returned(
        self, authenticate, user, grouped_by_date, mock_current_datetime
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 6)):
            entry1 = baker.make(HistoryEntry, profile=profile, video=video)
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 12)):
            entry2 = baker.make(HistoryEntry, profile=profile, video=video)
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 18)):
            entry3 = baker.make(HistoryEntry, profile=profile, video=video)
        with mock_current_datetime(timezone.datetime(2024, 1, 2, 6)):
            entry4 = baker.make(HistoryEntry, profile=profile, video=video)

        response = grouped_by_date("Europe/Amsterdam")

        assert response.status_code == status.HTTP_200_OK
        assert (
            entry1.creation_date.date()
            == entry2.creation_date.date()
            == entry3.creation_date.date()
        )
        assert entry4.creation_date.date() != entry1.creation_date.date()
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["date"] == entry4.creation_date.date()
        assert len(response.data["results"][0]["entries"]) == 1
        assert response.data["results"][0]["entries"][0]["id"] == entry4.id
        assert response.data["results"][1]["date"] == entry3.creation_date.date()
        assert len(response.data["results"][1]["entries"]) == 1
        assert response.data["results"][1]["entries"][0]["id"] == entry3.id

    def test_cursor_pagination(
        self,
        authenticate,
        user,
        grouped_by_date,
        mock_current_datetime,
        pagination,
        api_client,
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 6)):
            entry1 = baker.make(HistoryEntry, profile=profile)
        with mock_current_datetime(timezone.datetime(2024, 1, 1, 12)):
            entry2 = baker.make(HistoryEntry, profile=profile)
        with mock_current_datetime(timezone.datetime(2024, 1, 2, 6)):
            entry3 = baker.make(HistoryEntry, profile=profile)

        response1 = grouped_by_date(
            "Europe/Amsterdam", pagination=pagination(type="cursor", page_size=2)
        )
        response2 = api_client.get(response1.data["next"])

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert len(response1.data["results"][0]["entries"]) == 1
        assert response1.data["results"][0]["entries"][0]["id"] == entry3.id
        assert len(response1.data["results"][1]["entries"]) == 1
        assert response1.data["results"][1]["entries"][0]["id"] == entry2.id
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert len(response2.data["results"][0]["entries"]) == 1
        assert response2.data["results"][0]["entries"][0]["id"] == entry1.id


@pytest.mark.django_db
class TestRemoveVideoFromHistory:
    def test_if_user_is_anonymous_returns_401(self, remove_video_from_history):
        response = remove_video_from_history(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(
        self, authenticate, user, remove_video_from_history
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_video_from_history("a")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["video"] is not None

    def test_if_video_doesnt_exist_returns_400(
        self, authenticate, user, remove_video_from_history
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = remove_video_from_history(1)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_entry_doesnt_exist_returns_200(
        self, authenticate, user, remove_video_from_history
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)

        response = remove_video_from_history(video.id)

        assert response.status_code == status.HTTP_200_OK

    def test_deletes_entry(self, authenticate, user, remove_video_from_history):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        video = baker.make(Video)
        baker.make(HistoryEntry, video=video, profile=profile)
        initial_entry_count = HistoryEntry.objects.filter(video=video).count()

        response = remove_video_from_history(video.id)

        assert response.status_code == status.HTTP_200_OK
        assert initial_entry_count == 1
        assert HistoryEntry.objects.filter(video=video).count() == 0

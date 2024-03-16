from pathlib import Path
from time import sleep, time

import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework import status

from videos.models import Upload


LIST_VIEWNAME = "videos:uploads-list"
DETAIL_VIEWNAME = "videos:uploads-detail"
MAX_VIDEO_DURATION_SECONDS = 90
CURRENT_FOLDER = Path(__file__).parent


@pytest.fixture
def valid_video(generate_blank_video):
    with generate_blank_video(width=320, height=240, duration=1, format="mp4") as video:
        yield video


@pytest.fixture
def invalid_video(generate_blank_video):
    with generate_blank_video(width=320, height=240, duration=1, format="mkv") as video:
        yield video


@pytest.fixture
def too_long_video(generate_blank_video):
    with generate_blank_video(
        width=320, height=240, duration=MAX_VIDEO_DURATION_SECONDS + 1, format="mp4"
    ) as video:
        yield video


@pytest.fixture
def create_upload(create_object):
    def _create_upload(upload):
        return create_object(LIST_VIEWNAME, upload, format="multipart")

    return _create_upload


@pytest.fixture
def retrieve_upload(retrieve_object):
    def _retrieve_upload(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_upload


@pytest.fixture
def update_upload(update_object):
    def _update_upload(pk, upload):
        return update_object(DETAIL_VIEWNAME, pk, upload)

    return _update_upload


@pytest.fixture
def delete_upload(delete_object):
    def _delete_upload(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_upload


@pytest.fixture
def list_uploads(list_objects):
    def _list_uploads(*, filters=None, ordering=None, pagination=None):
        return list_objects(
            LIST_VIEWNAME, filters=filters, ordering=ordering, pagination=pagination
        )

    return _list_uploads


@pytest.mark.django_db
class TestCreateUpload:
    def test_if_user_is_anonymous_returns_401(self, create_upload):
        response = create_upload({"file": ""})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_returns_400(self, authenticate, user, create_upload):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_upload({"file": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["file"] is not None

    def test_if_video_extension_is_not_supported_returns_400(
        self, authenticate, user, create_upload, invalid_video
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_upload({"file": invalid_video})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["file"] is not None

    def test_if_video_is_too_long_returns_400(
        self, authenticate, user, create_upload, too_long_video
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_upload({"file": too_long_video})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["file"] is not None

    def test_if_video_is_valid_returns_201(
        self, authenticate, create_upload, valid_video, user
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_upload({"file": valid_video})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0

    @pytest.mark.django_db(transaction=True)
    def test_if_video_is_valid_processing_succeeds(
        self, authenticate, create_upload, valid_video, user, celery_worker
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_upload({"file": valid_video})
        upload_id = response.data["id"]
        upload = Upload.objects.get(id=upload_id)
        timer = time() + 20
        while not upload.is_done and time() < timer:
            upload.refresh_from_db()
            sleep(0.1)

        assert upload.is_done == True
        assert upload.video.id > 0

    @pytest.mark.django_db(transaction=True)
    def test_derives_video_title_from_filename(
        self, authenticate, create_upload, valid_video, user, celery_worker
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_upload({"file": valid_video})
        upload_id = response.data["id"]
        upload = Upload.objects.get(id=upload_id)
        timer = time() + 20
        while not upload.is_done and time() < timer:
            upload.refresh_from_db()
            sleep(0.1)

        assert upload.video.title != ""
        assert upload.video.title == Path(valid_video.name).stem

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.recommender
    def test_video_gets_inserted_in_recommender_system(
        self, authenticate, create_upload, valid_video, user, gorse, celery_worker
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = create_upload({"file": valid_video})
        upload_id = response.data["id"]
        upload = Upload.objects.get(id=upload_id)
        timer = time() + 20
        has_processed = False
        while not has_processed and time() < timer:
            sleep(1)
            items, _ = gorse.get_items(n=10)
            has_processed = len(items) > 0
        upload.refresh_from_db()

        assert len(items) == 1
        assert int(items[0]["ItemId"]) == upload.video.id


@pytest.mark.django_db
class TestRetrieveUpload:
    def test_if_user_is_anonymous_returns_401(self, retrieve_upload):
        response = retrieve_upload(1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_upload_doesnt_exist_returns_404(
        self, authenticate, user, retrieve_upload
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)

        response = retrieve_upload(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_upload_exists_and_user_doesnt_own_upload_returns_404(
        self, retrieve_upload, authenticate, user, other_user
    ):
        authenticate(user=user)
        baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        upload = baker.make(Upload, profile=other_profile)

        response = retrieve_upload(upload.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_upload_exists_and_user_owns_upload_returns_200(
        self, retrieve_upload, authenticate, user, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        upload = baker.make(Upload, profile=profile)

        response = retrieve_upload(upload.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": upload.id,
            "profile": profile.id,
            "creation_date": isoformat(upload.creation_date),
            "filename": upload.filename,
            "video": None,
            "is_done": False,
        }


@pytest.mark.django_db
class TestUpdateUpload:
    def test_returns_405(self, authenticate, update_upload):
        authenticate()

        response = update_upload(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteUpload:
    def test_returns_405(self, authenticate, delete_upload):
        authenticate()

        response = delete_upload(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestListUpload:
    def test_if_user_is_anonymous_returns_401(self, list_uploads):
        response = list_uploads()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_authenticated_returns_200(
        self, authenticate, user, list_uploads, isoformat
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        upload = baker.make(Upload, profile=profile)

        response = list_uploads()

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": upload.id,
            "profile": profile.id,
            "creation_date": isoformat(upload.creation_date),
            "filename": upload.filename,
            "video": None,
            "is_done": False,
        }

    def test_user_can_only_get_own_uploads(
        self, authenticate, user, other_user, list_uploads
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        other_profile = baker.make(settings.PROFILE_MODEL, user=other_user)
        upload1 = baker.make(Upload, profile=profile)
        upload2 = baker.make(Upload, profile=other_profile)

        response = list_uploads()

        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == upload1.id

    def test_filtering_by_filename(self, authenticate, user, list_uploads, filter):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        value = "test"
        upload1 = baker.make(Upload, profile=profile, filename=f"{value}1.mp4")
        upload2 = baker.make(Upload, profile=profile, filename=f"{value}2.mp4")
        upload3 = baker.make(Upload, profile=profile, filename="abc.mp4")

        response = list_uploads(
            filters=[filter(field="filename", lookup_type="icontains", value=value)]
        )

        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == upload1.id
        assert response.data["results"][1]["id"] == upload2.id

    def test_filtering_by_is_done(self, authenticate, user, list_uploads, filter):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        upload1 = baker.make(Upload, profile=profile, is_done=True)
        upload2 = baker.make(Upload, profile=profile, is_done=True)
        upload3 = baker.make(Upload, profile=profile, is_done=False)

        response = list_uploads(
            filters=[filter(field="is_done", lookup_type="exact", value="true")]
        )

        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["id"] == upload1.id
        assert response.data["results"][1]["id"] == upload2.id

    def test_ordering_by_filename(self, authenticate, user, list_uploads, ordering):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        upload1 = baker.make(Upload, profile=profile, filename="c.mp4")
        upload2 = baker.make(Upload, profile=profile, filename="a.mp4")
        upload3 = baker.make(Upload, profile=profile, filename="b.mp4")

        response1 = list_uploads(ordering=ordering(field="filename", direction="ASC"))
        response2 = list_uploads(ordering=ordering(field="filename", direction="DESC"))

        assert response1.data["results"][0]["id"] == upload2.id
        assert response1.data["results"][1]["id"] == upload3.id
        assert response1.data["results"][2]["id"] == upload1.id
        assert response2.data["results"][0]["id"] == upload1.id
        assert response2.data["results"][1]["id"] == upload3.id
        assert response2.data["results"][2]["id"] == upload2.id

    def test_ordering_by_creation_date(
        self, authenticate, user, list_uploads, ordering
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        upload1 = baker.make(Upload, profile=profile)
        sleep(0.0001)
        upload2 = baker.make(Upload, profile=profile)
        sleep(0.0001)
        upload3 = baker.make(Upload, profile=profile)

        response1 = list_uploads(
            ordering=ordering(field="creation_date", direction="ASC")
        )
        response2 = list_uploads(
            ordering=ordering(field="creation_date", direction="DESC")
        )

        assert response1.data["results"][0]["id"] == upload1.id
        assert response1.data["results"][1]["id"] == upload2.id
        assert response1.data["results"][2]["id"] == upload3.id
        assert response2.data["results"][0]["id"] == upload3.id
        assert response2.data["results"][1]["id"] == upload2.id
        assert response2.data["results"][2]["id"] == upload1.id

    def test_ordering_by_is_done(self, authenticate, user, list_uploads, ordering):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        upload1 = baker.make(Upload, profile=profile, is_done=False)
        upload2 = baker.make(Upload, profile=profile, is_done=True)
        upload3 = baker.make(Upload, profile=profile, is_done=True)

        response1 = list_uploads(ordering=ordering(field="is_done", direction="ASC"))
        response2 = list_uploads(ordering=ordering(field="is_done", direction="DESC"))

        assert response1.data["results"][0]["id"] == upload1.id
        assert response1.data["results"][1]["id"] == upload2.id
        assert response1.data["results"][2]["id"] == upload3.id
        assert response2.data["results"][0]["id"] == upload2.id
        assert response2.data["results"][1]["id"] == upload3.id
        assert response2.data["results"][2]["id"] == upload1.id

    def test_limit_offset_pagination(
        self, authenticate, user, list_uploads, pagination
    ):
        authenticate(user=user)
        profile = baker.make(settings.PROFILE_MODEL, user=user)
        uploads = [baker.make(Upload, profile=profile) for i in range(3)]

        response1 = list_uploads(pagination=pagination(type="limit_offset", limit=2))
        response2 = list_uploads(
            pagination=pagination(type="limit_offset", limit=2, offset=2)
        )

        assert response1.data["count"] == 3
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == uploads[0].id
        assert response1.data["results"][1]["id"] == uploads[1].id
        assert response2.data["count"] == 3
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == uploads[2].id

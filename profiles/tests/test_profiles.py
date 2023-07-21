from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from profiles.models import Profile


@pytest.fixture
def create_profile(api_client):
    def do_create_profile(profile):
        return api_client.post(reverse("profiles:api-root") + "profiles/", profile)

    return do_create_profile


@pytest.fixture
def retrieve_profile(api_client):
    def do_retrieve_profile(id):
        return api_client.get(reverse("profiles:profiles-detail", kwargs={"pk": id}))

    return do_retrieve_profile


@pytest.fixture
def update_profile(api_client):
    def do_update_profile(id, profile):
        return api_client.patch(
            reverse("profiles:profiles-detail", kwargs={"pk": id}), profile
        )

    return do_update_profile


@pytest.fixture
def delete_profile(api_client):
    def do_delete_profile(id):
        return api_client.delete(reverse("profiles:profiles-detail", kwargs={"pk": id}))

    return do_delete_profile


@pytest.fixture
def list_profiles(api_client):
    def do_list_profiles():
        return api_client.get(reverse("profiles:api-root") + "profiles/")

    return do_list_profiles


@pytest.fixture
def retrieve_own_profile(api_client):
    def do_retrieve_own_profile():
        return api_client.get(reverse("profiles:profiles-me"))

    return do_retrieve_own_profile


@pytest.fixture
def update_own_profile(api_client):
    def do_update_own_profile(profile, format="multipart"):
        return api_client.patch(reverse("profiles:profiles-me"), profile, format=format)

    return do_update_own_profile


@pytest.fixture
def retrieve_profile_by_username(api_client):
    def do_retrieve_profile_by_username(username):
        return api_client.get(
            reverse(
                "profiles:profiles-retrieve-by-username", kwargs={"username": username}
            )
        )

    return do_retrieve_profile_by_username


class TestCreateProfile:
    def test_returns_404(self, create_profile):
        response = create_profile({})

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRetrieveProfile:
    def test_if_profile_doesnt_exist_returns_404(self, retrieve_profile):
        response = retrieve_profile(1)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_profile_exists_returns_200(self, retrieve_profile):
        profile = baker.make(Profile)

        response = retrieve_profile(profile.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": profile.id,
            "user": {"id": profile.user.id, "username": profile.user.username},
            "full_name": profile.full_name,
            "description": profile.description,
            "avatar": profile.avatar,
        }


class TestUpdateProfile:
    def test_returns_405(self, update_profile):
        response = update_profile(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestDeleteProfile:
    def test_returns_405(self, delete_profile):
        response = delete_profile(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestListProfiles:
    def test_returns_404(self, list_profiles):
        response = list_profiles()

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRetrieveOwnProfile:
    def test_if_user_is_anonymous_returns_401(self, retrieve_own_profile):
        response = retrieve_own_profile()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_doesnt_have_profile_returns_404(
        self, authenticate, user, retrieve_own_profile
    ):
        authenticate(user=user)

        response = retrieve_own_profile()

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_user_has_profile_returns_200(
        self, authenticate, user, retrieve_own_profile
    ):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)

        response = retrieve_own_profile()

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": profile.id,
            "user": {"id": user.id, "username": user.username},
            "full_name": profile.full_name,
            "description": profile.description,
            "avatar": profile.avatar,
        }


@pytest.mark.django_db
class TestUpdateOwnProfile:
    def test_if_user_is_anonymous_returns_401(self, update_own_profile):
        response = update_own_profile({})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_doesnt_have_profile_returns_404(
        self, authenticate, user, update_own_profile
    ):
        authenticate(user=user)

        response = update_own_profile({})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_change_user(
        self, authenticate, user, other_user, update_own_profile
    ):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)

        response = update_own_profile({"user": other_user.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": profile.id,
            "user": {"id": user.id, "username": user.username},
            "full_name": profile.full_name,
            "description": profile.description,
            "avatar": profile.avatar,
        }

    def test_if_data_is_invalid_returns_400(
        self, authenticate, user, update_own_profile
    ):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)

        response = update_own_profile(
            {"full_name": "", "description": None, "avatar": 1}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["full_name"] is not None
        assert response.data["description"] is not None
        assert response.data["avatar"] is not None

    def test_if_data_is_valid_returns_200(
        self,
        authenticate,
        user,
        generate_blank_image,
        update_own_profile,
        is_valid_image,
    ):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)
        new_full_name = "a"
        new_description = "b"
        new_avatar = generate_blank_image(width=100, height=100, format="PNG")

        response = update_own_profile(
            {
                "full_name": new_full_name,
                "description": new_description,
                "avatar": new_avatar,
            }
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": profile.id,
            "user": {"id": user.id, "username": user.username},
            "full_name": new_full_name,
            "description": new_description,
            "avatar": response.data["avatar"],
        }
        assert is_valid_image(response.data["avatar"])

    def test_avatar_file_gets_random_name(
        self,
        authenticate,
        user,
        generate_blank_image,
        update_own_profile,
    ):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)
        filename = "testfilename"
        new_avatar = generate_blank_image(
            width=100, height=100, format="PNG", filename=filename
        )

        response = update_own_profile({"avatar": new_avatar})
        filename_after_update = Path(response.data["avatar"]).stem

        assert filename not in filename_after_update

    def test_avatar_gets_converted_to_jpg(
        self,
        authenticate,
        user,
        generate_blank_image,
        update_own_profile,
    ):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)
        new_avatar = generate_blank_image(width=100, height=100, format="PNG")

        response = update_own_profile({"avatar": new_avatar})
        avatar_extension = Path(response.data["avatar"]).suffix[1:]

        assert avatar_extension == "jpg"


@pytest.mark.django_db
class TestRetrieveProfileByUsername:
    def test_if_profile_doesnt_exist_returns_404(self, retrieve_profile_by_username):
        response = retrieve_profile_by_username("username")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_profile_exists_returns_200(self, retrieve_profile_by_username):
        profile = baker.make(Profile)

        response = retrieve_profile_by_username(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": profile.id,
            "user": {"id": profile.user.id, "username": profile.user.username},
            "full_name": profile.full_name,
            "description": profile.description,
            "avatar": profile.avatar,
        }

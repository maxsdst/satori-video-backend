from pathlib import Path
from time import sleep

import pytest
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from profiles.models import Follow, Profile


DETAIL_VIEWNAME = "profiles:profiles-detail"


@pytest.fixture
def create_profile(api_client):
    def _create_profile(profile):
        return api_client.post(reverse("profiles:api-root") + "profiles/", profile)

    return _create_profile


@pytest.fixture
def retrieve_profile(retrieve_object):
    def _retrieve_profile(pk):
        return retrieve_object(DETAIL_VIEWNAME, pk)

    return _retrieve_profile


@pytest.fixture
def update_profile(update_object):
    def _update_profile(pk, profile):
        return update_object(DETAIL_VIEWNAME, pk, profile)

    return _update_profile


@pytest.fixture
def delete_profile(delete_object):
    def _delete_profile(pk):
        return delete_object(DETAIL_VIEWNAME, pk)

    return _delete_profile


@pytest.fixture
def list_profiles(api_client):
    def _list_profiles():
        return api_client.get(reverse("profiles:api-root") + "profiles/")

    return _list_profiles


@pytest.fixture
def retrieve_own_profile(api_client):
    def _retrieve_own_profile():
        return api_client.get(reverse("profiles:profiles-me"))

    return _retrieve_own_profile


@pytest.fixture
def update_own_profile(api_client):
    def _update_own_profile(profile, format="multipart"):
        return api_client.patch(reverse("profiles:profiles-me"), profile, format=format)

    return _update_own_profile


@pytest.fixture
def retrieve_profile_by_username(api_client):
    def _retrieve_profile_by_username(username):
        return api_client.get(
            reverse(
                "profiles:profiles-retrieve-by-username", kwargs={"username": username}
            )
        )

    return _retrieve_profile_by_username


@pytest.fixture
def search(list_objects):
    def _search(query: str, pagination=None):
        return list_objects(
            "profiles:profiles-search",
            {"query": query},
            pagination=pagination,
        )

    return _search


@pytest.fixture
def follow(api_client):
    def _follow(username):
        return api_client.post(
            reverse("profiles:profiles-follow", kwargs={"username": username})
        )

    return _follow


@pytest.fixture
def unfollow(api_client):
    def _unfollow(username):
        return api_client.post(
            reverse("profiles:profiles-unfollow", kwargs={"username": username})
        )

    return _unfollow


@pytest.fixture
def following(list_objects):
    def _following(username, *, pagination=None):
        return list_objects(
            "profiles:profiles-following",
            reverse_kwargs={"username": username},
            pagination=pagination,
        )

    return _following


@pytest.fixture
def followers(list_objects):
    def _followers(username, *, pagination=None):
        return list_objects(
            "profiles:profiles-followers",
            reverse_kwargs={"username": username},
            pagination=pagination,
        )

    return _followers


@pytest.mark.django_db
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
            "following_count": 0,
            "follower_count": 0,
            "is_following": False,
        }

    def test_following_count(self, retrieve_profile):
        profile1 = baker.make(Profile)
        profile2 = baker.make(Profile)
        baker.make(Follow, follower=profile2)

        response1 = retrieve_profile(profile1.id)
        response2 = retrieve_profile(profile2.id)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["following_count"] == 0
        assert response2.data["following_count"] == 1

    def test_follower_count(self, retrieve_profile):
        profile1 = baker.make(Profile)
        profile2 = baker.make(Profile)
        baker.make(Follow, followed=profile2)

        response1 = retrieve_profile(profile1.id)
        response2 = retrieve_profile(profile2.id)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["follower_count"] == 0
        assert response2.data["follower_count"] == 1

    def test_following_status(self, authenticate, user, retrieve_profile):
        authenticate(user=user)
        own_profile = baker.make(Profile, user=user)
        profile1 = baker.make(Profile)
        profile2 = baker.make(Profile)
        baker.make(Follow, follower=own_profile, followed=profile2)

        response1 = retrieve_profile(profile1.id)
        response2 = retrieve_profile(profile2.id)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["is_following"] == False
        assert response2.data["is_following"] == True


@pytest.mark.django_db
class TestUpdateProfile:
    def test_returns_405(self, update_profile):
        response = update_profile(1, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeleteProfile:
    def test_returns_405(self, delete_profile):
        response = delete_profile(1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
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
            "following_count": 0,
            "follower_count": 0,
            "is_following": False,
        }


@pytest.mark.django_db(transaction=True)
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
            "following_count": 0,
            "follower_count": 0,
            "is_following": False,
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
            "following_count": 0,
            "follower_count": 0,
            "is_following": False,
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
            "following_count": 0,
            "follower_count": 0,
            "is_following": False,
        }


@pytest.mark.django_db
class TestSearch:
    def test_if_query_is_empty_returns_400(self, search):
        response = search("  ")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] is not None

    def test_returns_profiles(self, create_user, search):
        user = create_user("ab_test_c")
        profile = baker.make(Profile, user=user)

        response = search("test")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": profile.id,
            "user": {"id": user.id, "username": user.username},
            "full_name": profile.full_name,
            "description": profile.description,
            "avatar": profile.avatar.url if profile.avatar else None,
            "following_count": 0,
            "follower_count": 0,
            "is_following": False,
        }

    def test_filters_profiles(self, search):
        profile1 = baker.make(Profile, full_name="123")
        profile2 = baker.make(Profile, full_name="test")
        profile3 = baker.make(Profile, full_name="abc")

        response = search("test")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == profile2.id

    def test_searches_by_username(self, create_user, search):
        user = create_user("ab_test_c")
        profile = baker.make(Profile, user=user)

        response = search("test")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == profile.id

    def test_searches_by_full_name(self, search):
        profile = baker.make(Profile, full_name="abc test 123")

        response = search("test")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == profile.id

    def test_search_is_case_insensitive(self, search):
        profile = baker.make(Profile, full_name="abc TeSt 123")

        response = search("tEsT")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == profile.id

    def test_query_string_gets_normalized(self, search):
        profile = baker.make(Profile, full_name="abc test 123")

        response = search("  c   test  1 ")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == profile.id

    def test_cursor_pagination(self, search, pagination, api_client):
        profiles = [baker.make(Profile, full_name="test") for i in range(3)]

        response1 = search("test", pagination=pagination(type="cursor", page_size=2))
        response2 = api_client.get(response1.data["next"])

        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == profiles[0].id
        assert response1.data["results"][1]["id"] == profiles[1].id
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == profiles[2].id


@pytest.mark.django_db
class TestFollow:
    def test_if_user_is_anonymous_returns_401(self, follow):
        response = follow("a")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_profile_doesnt_exist_returns_404(self, authenticate, user, follow):
        authenticate(user=user)
        baker.make(Profile, user=user)

        response = follow("a")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_follow_own_profile(self, authenticate, user, follow):
        authenticate(user=user)
        profile = baker.make(Profile, user=user)

        response = follow(profile.user.username)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] is not None

    def test_creates_follow(self, authenticate, user, follow):
        authenticate(user=user)
        own_profile = baker.make(Profile, user=user)
        profile = baker.make(Profile)
        initial_count = Follow.objects.filter(
            follower=own_profile, followed=profile
        ).count()

        response = follow(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert initial_count == 0
        assert (
            Follow.objects.filter(follower=own_profile, followed=profile).count() == 1
        )

    def test_cannot_follow_profile_multiple_times(self, authenticate, user, follow):
        authenticate(user=user)
        baker.make(Profile, user=user)
        profile = baker.make(Profile)

        response1 = follow(profile.user.username)
        response2 = follow(profile.user.username)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.data["detail"] is not None


@pytest.mark.django_db
class TestUnfollow:
    def test_if_user_is_anonymous_returns_401(self, unfollow):
        response = unfollow("a")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_profile_doesnt_exist_returns_404(self, authenticate, user, unfollow):
        authenticate(user=user)
        baker.make(Profile, user=user)

        response = unfollow("a")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_follow_doesnt_exist_returns_200(self, authenticate, user, unfollow):
        authenticate(user=user)
        baker.make(Profile, user=user)
        profile = baker.make(Profile)

        response = unfollow(profile.user.username)

        assert response.status_code == status.HTTP_200_OK

    def test_deletes_follow(self, authenticate, user, unfollow):
        authenticate(user=user)
        own_profile = baker.make(Profile, user=user)
        profile = baker.make(Profile)
        baker.make(Follow, follower=own_profile, followed=profile)
        initial_count = Follow.objects.filter(
            follower=own_profile, followed=profile
        ).count()

        response = unfollow(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert initial_count == 1
        assert (
            Follow.objects.filter(follower=own_profile, followed=profile).count() == 0
        )


@pytest.mark.django_db
class TestFollowing:
    def test_if_profile_doesnt_exist_returns_404(self, authenticate, user, following):
        authenticate(user=user)
        baker.make(Profile, user=user)

        response = following("a")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_profiles(self, following):
        profile = baker.make(Profile)
        other_profile = baker.make(Profile)
        baker.make(Follow, follower=profile, followed=other_profile)

        response = following(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": other_profile.id,
            "user": {
                "id": other_profile.user.id,
                "username": other_profile.user.username,
            },
            "full_name": other_profile.full_name,
            "description": other_profile.description,
            "avatar": other_profile.avatar.url if other_profile.avatar else None,
            "following_count": 0,
            "follower_count": 1,
            "is_following": False,
        }

    def test_returns_only_followed_profiles(self, following):
        profile = baker.make(Profile)
        other_profile1 = baker.make(Profile)
        other_profile2 = baker.make(Profile)
        other_profile3 = baker.make(Profile)
        other_profile4 = baker.make(Profile)
        baker.make(Follow, follower=profile, followed=other_profile2)
        baker.make(Follow, follower=profile, followed=other_profile3)

        response = following(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert set([x["id"] for x in response.data["results"]]) == set(
            [other_profile2.id, other_profile3.id]
        )

    def test_profiles_ordered_by_follow_date(self, following):
        profile = baker.make(Profile)
        other_profile1 = baker.make(Profile)
        other_profile2 = baker.make(Profile)
        other_profile3 = baker.make(Profile)
        baker.make(Follow, follower=profile, followed=other_profile2)
        sleep(0.01)
        baker.make(Follow, follower=profile, followed=other_profile3)
        sleep(0.01)
        baker.make(Follow, follower=profile, followed=other_profile1)

        response = following(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == other_profile1.id
        assert response.data["results"][1]["id"] == other_profile3.id
        assert response.data["results"][2]["id"] == other_profile2.id

    def test_cursor_pagination(self, following, pagination, api_client):
        profile = baker.make(Profile)
        other_profiles = baker.make(Profile, _quantity=3)
        for other_profile in other_profiles:
            sleep(0.01)
            baker.make(Follow, follower=profile, followed=other_profile)

        response1 = following(
            profile.user.username, pagination=pagination(type="cursor", page_size=2)
        )
        response2 = api_client.get(response1.data["next"])

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == other_profiles[2].id
        assert response1.data["results"][1]["id"] == other_profiles[1].id
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == other_profiles[0].id


@pytest.mark.django_db
class TestFollowers:
    def test_if_profile_doesnt_exist_returns_404(self, authenticate, user, followers):
        authenticate(user=user)
        baker.make(Profile, user=user)

        response = followers("a")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_profiles(self, followers):
        profile = baker.make(Profile)
        other_profile = baker.make(Profile)
        baker.make(Follow, follower=other_profile, followed=profile)

        response = followers(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0] == {
            "id": other_profile.id,
            "user": {
                "id": other_profile.user.id,
                "username": other_profile.user.username,
            },
            "full_name": other_profile.full_name,
            "description": other_profile.description,
            "avatar": other_profile.avatar.url if other_profile.avatar else None,
            "following_count": 1,
            "follower_count": 0,
            "is_following": False,
        }

    def test_returns_only_followers(self, followers):
        profile = baker.make(Profile)
        other_profile1 = baker.make(Profile)
        other_profile2 = baker.make(Profile)
        other_profile3 = baker.make(Profile)
        other_profile4 = baker.make(Profile)
        baker.make(Follow, follower=other_profile2, followed=profile)
        baker.make(Follow, follower=other_profile3, followed=profile)

        response = followers(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert set([x["id"] for x in response.data["results"]]) == set(
            [other_profile2.id, other_profile3.id]
        )

    def test_profiles_ordered_by_follow_date(self, followers):
        profile = baker.make(Profile)
        other_profile1 = baker.make(Profile)
        other_profile2 = baker.make(Profile)
        other_profile3 = baker.make(Profile)
        baker.make(Follow, follower=other_profile2, followed=profile)
        sleep(0.01)
        baker.make(Follow, follower=other_profile3, followed=profile)
        sleep(0.01)
        baker.make(Follow, follower=other_profile1, followed=profile)

        response = followers(profile.user.username)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == other_profile1.id
        assert response.data["results"][1]["id"] == other_profile3.id
        assert response.data["results"][2]["id"] == other_profile2.id

    def test_cursor_pagination(self, followers, pagination, api_client):
        profile = baker.make(Profile)
        other_profiles = baker.make(Profile, _quantity=3)
        for other_profile in other_profiles:
            sleep(0.01)
            baker.make(Follow, follower=other_profile, followed=profile)

        response1 = followers(
            profile.user.username, pagination=pagination(type="cursor", page_size=2)
        )
        response2 = api_client.get(response1.data["next"])

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["previous"] is None
        assert response1.data["next"] is not None
        assert len(response1.data["results"]) == 2
        assert response1.data["results"][0]["id"] == other_profiles[2].id
        assert response1.data["results"][1]["id"] == other_profiles[1].id
        assert response2.data["previous"] is not None
        assert response2.data["next"] is None
        assert len(response2.data["results"]) == 1
        assert response2.data["results"][0]["id"] == other_profiles[0].id

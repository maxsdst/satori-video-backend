from time import sleep, time

import pytest


LIST_VIEWNAME = "user-list"
DETAIL_VIEWNAME = "user-detail"


@pytest.fixture
def create_user(create_object):
    def _create_user(user):
        return create_object(LIST_VIEWNAME, user, format="json")

    return _create_user


@pytest.mark.django_db
class TestCreateUser:
    @pytest.mark.django_db(transaction=True)
    @pytest.mark.recommender
    def test_user_gets_inserted_in_recommender_system(
        self, create_user, gorse, celery_worker
    ):
        response = create_user(
            {
                "email": "123@email.com",
                "full_name": "a",
                "username": "b",
                "password": "Abc123Abc123&&&",
            }
        )
        timer = time() + 20
        has_processed = False
        while not has_processed and time() < timer:
            sleep(1)
            users, _ = gorse.get_users(n=10)
            has_processed = len(users) > 0

        assert len(users) == 1
        assert int(users[0]["UserId"]) == response.data["id"]

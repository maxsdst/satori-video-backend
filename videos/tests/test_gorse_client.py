import pytest


@pytest.mark.recommender
class TestGetUsers:
    def test_returns_users(self, gorse):
        user = {
            "Comment": "a",
            "Labels": ["b", "c"],
            "Subscribe": [],
            "UserId": "1",
        }
        gorse.insert_user(user)

        users, _ = gorse.get_users(n=10)

        assert users == [user]

    def test_pagination(self, gorse):
        gorse.insert_users(
            [
                {
                    "Comment": "",
                    "Labels": [],
                    "Subscribe": [],
                    "UserId": str(i),
                }
                for i in range(3)
            ]
        )

        users1, cursor1 = gorse.get_users(n=2)
        users2, cursor2 = gorse.get_users(n=2, cursor=cursor1)

        assert len(users1) == 2
        assert cursor1
        assert len(users2) == 1
        assert cursor2 == ""


@pytest.mark.recommender
class TestInsertUsers:
    def test_inserts_users(self, gorse):
        initial_users, _ = gorse.get_users(n=10)
        users_to_insert = [
            {
                "Comment": "a",
                "Labels": ["b", "c"],
                "Subscribe": [],
                "UserId": "1",
            },
            {
                "Comment": "d",
                "Labels": ["e", "f"],
                "Subscribe": [],
                "UserId": "2",
            },
        ]

        response = gorse.insert_users(users_to_insert)
        users, _ = gorse.get_users(n=10)

        assert response == {"RowAffected": 2}
        assert len(initial_users) == 0
        assert users == users_to_insert


@pytest.mark.recommender
class TestInsertItems:
    def test_inserts_items(self, gorse):
        initial_items, _ = gorse.get_items(n=10)
        items_to_insert = [
            {
                "Categories": ["a", "b"],
                "Comment": "c",
                "IsHidden": False,
                "ItemId": "1",
                "Labels": ["d", "e"],
                "Timestamp": "2020-02-02T20:20:02Z",
            },
            {
                "Categories": ["f", "g"],
                "Comment": "h",
                "IsHidden": False,
                "ItemId": "2",
                "Labels": ["i", "j"],
                "Timestamp": "2020-02-02T20:20:02Z",
            },
        ]

        response = gorse.insert_items(items_to_insert)
        items, _ = gorse.get_items(n=10)

        assert response == {"RowAffected": 2}
        assert len(initial_items) == 0
        assert items == items_to_insert


@pytest.mark.recommender
class TestGetPopular:
    def test_returns_popular_items(self, gorse):
        items = gorse.get_popular(10, 0)

        assert items == []
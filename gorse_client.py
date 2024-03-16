from django.conf import settings

from gorse import Gorse


class GorseClient(Gorse):
    """Extends default Gorse client to include missing methods."""

    # bypass name mangling
    __request = getattr(Gorse, f"_{Gorse.__name__}__request")

    def get_users(self, n: int, cursor: str = "") -> tuple[list[dict], str]:
        """Get users.
        :param n: number of returned users
        :param cursor: cursor for next page
        :return: users and cursor for next page
        """

        params = {"n": n, "cursor": cursor}
        response = self.__request("GET", f"{self.entry_point}/api/users", params=params)
        return response["Users"], response["Cursor"]

    def insert_users(self, users: list[dict]) -> dict:
        """Insert users."""

        return self.__request("POST", f"{self.entry_point}/api/users", json=users)

    def insert_items(self, items: list[dict]) -> dict:
        """Insert items."""

        return self.__request("POST", f"{self.entry_point}/api/items", json=items)

    def get_popular(self, n: int, offset: int, user_id: str = None) -> list[dict]:
        """Get popular items."""

        params = {"n": n, "offset": offset}
        if user_id:
            params["user-id"] = user_id

        return self.__request("GET", f"{self.entry_point}/api/popular", params=params)


def get_gorse_client() -> GorseClient:
    """Get instance of Gorse client."""

    return GorseClient(settings.GORSE_ENTRY_POINT, settings.GORSE_API_KEY, 10)

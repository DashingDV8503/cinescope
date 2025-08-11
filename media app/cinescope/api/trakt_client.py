import requests

BASE_URL = "https://api.trakt.tv"

class TraktClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("A Trakt.tv API key is required.")
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": self.api_key
        }

    def get_trending_movies(self):
        return self._make_request("/movies/trending")

    def get_popular_movies(self):
        return self._make_request("/movies/popular")

    def get_trending_shows(self):
        return self._make_request("/shows/trending")

    def get_popular_shows(self):
        return self._make_request("/shows/popular")

    def _make_request(self, endpoint):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"An error occurred with Trakt.tv API ({endpoint}): {e}")
            return None

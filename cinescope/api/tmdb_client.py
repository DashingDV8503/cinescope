import requests

BASE_URL = "https://api.themoviedb.org/3"

class TMDbClient:
    def __init__(self, api_key: str):
        if not api_key: raise ValueError("An API key is required.")
        self.api_key = api_key

    def _make_request(self, endpoint, params=None):
        """Helper function to make requests and handle errors."""
        if params is None:
            params = {}
        # Every request needs the api_key
        params["api_key"] = self.api_key

        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"An error occurred with TMDb API ({endpoint}): {e}")
            return None

    def search_multi(self, query: str):
        return self._make_request("search/multi", {"query": query, "include_adult": False})

    def find_by_imdb_id(self, imdb_id: str):
        return self._make_request(f"find/{imdb_id}", {"external_source": "imdb_id"})

    def get_details(self, media_type: str, tmdb_id: int):
        # 'movie' or 'tv'
        endpoint = f"{media_type}/{tmdb_id}"
        return self._make_request(endpoint, {"append_to_response": "external_ids"})
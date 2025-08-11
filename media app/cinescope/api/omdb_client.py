import requests

BASE_URL = "https://www.omdbapi.com/"

class OMDbClient:
    def __init__(self, api_key: str):
        if not api_key: raise ValueError("An API key is required.")
        self.api_key = api_key

    def search(self, query: str):
        params = {"s": query, "apikey": self.api_key}
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("Response") == "True":
                return data.get("Search", [])
            return []
        except requests.RequestException as e:
            print(f"An error occurred with OMDb API: {e}")
            return []
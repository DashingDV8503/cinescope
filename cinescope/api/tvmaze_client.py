import requests

BASE_URL = "https://api.tvmaze.com"

class TVMazeClient:
    def search_shows(self, query: str):
        try:
            response = requests.get(f"{BASE_URL}/search/shows", params={"q": query})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"An error occurred with TVMaze API (search/shows): {e}")
            return None

    def get_show_episodes(self, show_id: int):
        try:
            response = requests.get(f"{BASE_URL}/shows/{show_id}?embed=episodes")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"An error occurred with TVMaze API (shows/{show_id}): {e}")
            return None

import os
from dotenv import load_dotenv

def get_api_keys():
    """
    Loads API keys from the .env file in the project root.
    """
    # The path to the project root directory
    project_dir = os.path.join(os.path.dirname(__file__), '..', '..')
    dotenv_path = os.path.join(project_dir, '.env')

    load_dotenv(dotenv_path=dotenv_path)

    return {
        "tmdb": os.getenv("TMDB_API_KEY"),
        "omdb": os.getenv("OMDB_API_KEY"),
        "trakt": os.getenv("TRAKT_API_KEY"),
    }
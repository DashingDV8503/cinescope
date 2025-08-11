import json
import os
from typing import List, Set
from PySide6.QtCore import QObject, Signal
from .media import Media, MediaStatus

class DataManager(QObject):
    list_updated = Signal()

    def __init__(self, filename="my_list.json"):
        super().__init__()
        # The file will be stored in the project root (C:\media app)
        self.filepath = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', filename
        ))
        self.my_list: List[Media] = []
        self.my_list_ids: Set[int] = set()
        self.load_list()

    def load_list(self):
        """Loads the media list from the JSON file if it exists."""
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r') as f:
                    # We need to reconstruct the list of Media objects
                    data = json.load(f)
                    self.my_list = [Media(**item) for item in data]
                    self.my_list_ids = {item.id for item in self.my_list}
                    print(f"Loaded {len(self.my_list)} items from {self.filepath}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error loading or parsing {self.filepath}: {e}")
            self.my_list = []
            self.my_list_ids = set()

    def save_list(self):
        """Saves the current media list to the JSON file."""
        with open(self.filepath, 'w') as f:
            # Convert list of Media objects to list of dictionaries
            data_to_save = [item.__dict__ for item in self.my_list]
            json.dump(data_to_save, f, indent=4, default=str)
        print(f"Saved {len(self.my_list)} items to {self.filepath}")
        self.list_updated.emit()

    def add_media(self, new_media: Media):
        """Adds a new media item to the list and saves."""
        if new_media.id not in self.my_list_ids:
            self.my_list.append(new_media)
            self.my_list_ids.add(new_media.id)
            self.save_list()
            return True
        print(f"Item '{new_media.title}' is already in the list.")
        return False

    def get_list(self) -> List[Media]:
        """Returns the full list of media objects."""
        return self.my_list

    def get_list_ids(self) -> Set[int]:
        """Returns a set of all media IDs for quick lookups."""
        return self.my_list_ids

    def get_media_by_id(self, media_id: int) -> Media | None:
        """Returns a media object from the list by its ID."""
        for media in self.my_list:
            if media.id == media_id:
                return media
        return None

    def update_media_status(self, media_id: int, new_status: MediaStatus):
        """Updates the status of a media item and saves the list."""
        for media in self.my_list:
            if media.id == media_id:
                media.status = new_status
                self.save_list()
                print(f"Updated status of '{media.title}' to '{new_status.value}'")
                return True
        return False

    def update_media_seasons(self, media_id: int, seasons: dict):
        """Updates the seasons of a media item and saves the list."""
        for media in self.my_list:
            if media.id == media_id:
                media.seasons = seasons
                self.save_list()
                print(f"Updated seasons of '{media.title}'")
                return True
        return False
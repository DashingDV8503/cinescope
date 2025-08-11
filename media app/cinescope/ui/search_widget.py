import sys
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QScrollArea, QGridLayout
)
from cinescope.api.tmdb_client import TMDbClient
from cinescope.api.omdb_client import OMDbClient
from cinescope.core.media import Media, MediaStatus, SeasonProgress
from cinescope.core.config import get_api_keys
from cinescope.core.data_manager import DataManager
from cinescope.ui.widgets import MediaCard

class SearchWidget(QWidget):
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.api_keys = get_api_keys()
        self.tmdb_client = TMDbClient(api_key=self.api_keys.get("tmdb"))
        self.omdb_client = OMDbClient(api_key=self.api_keys.get("omdb"))
        self.imdb_pattern = re.compile(r"^tt\d+$")

        layout = QVBoxLayout(self)

        controls_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by title or IMDb ID...")
        controls_layout.addWidget(self.search_bar)
        layout.addLayout(controls_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.results_container = QWidget()
        self.results_grid = QGridLayout(self.results_container)
        scroll_area.setWidget(self.results_container)

        self.search_bar.returnPressed.connect(self._on_search_triggered)
        self.displayed_cards = {}

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.displayed_cards = {}

    def _display_results(self, results):
        self._clear_layout(self.results_grid)
        unique_results = {str(r['id']): r for r in results}.values()
        my_list_ids = self.data_manager.get_list_ids()
        row, col = 0, 0
        for result in unique_results:
            tmdb_id = result.get("id")
            is_added = tmdb_id in my_list_ids
            card = MediaCard(result, is_added=is_added)
            card.add_media_requested.connect(self._on_add_media)
            self.results_grid.addWidget(card, row, col)
            self.displayed_cards[tmdb_id] = card
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def _perform_omdb_fallback(self, query):
        omdb_results = self.omdb_client.search(query)
        final_results = []
        for res in omdb_results:
            if imdb_id := res.get("imdbID"):
                tmdb_data = self.tmdb_client.find_by_imdb_id(imdb_id)
                if tmdb_data:
                    final_results.extend(tmdb_data.get("movie_results", []) + tmdb_data.get("tv_results", []))
        return final_results
        
    def _on_search_triggered(self):
        query = self.search_bar.text().strip()
        if not query: return
        final_results = []
        if self.imdb_pattern.match(query):
            data = self.tmdb_client.find_by_imdb_id(query)
            if data: final_results = data.get("movie_results", []) + data.get("tv_results", [])
        else:
            data = self.tmdb_client.search_multi(query)
            if data and data.get("results"):
                final_results = data["results"]
            else:
                final_results = self._perform_omdb_fallback(query)
        filtered_results = [r for r in final_results if r.get("media_type") in ["movie", "tv"] and r.get("poster_path")]
        self._display_results(filtered_results)
    
    def _on_add_media(self, search_result: dict):
        media_type = search_result.get("media_type", "movie")
        tmdb_id = search_result.get("id")
        if not tmdb_id: return
        details = self.tmdb_client.get_details(media_type, tmdb_id)
        if not details: return

        seasons_data = {}
        if media_type == 'tv' and 'seasons' in details:
            for season in details['seasons']:
                seasons_data[str(season['season_number'])] = SeasonProgress(
                    episodesWatched=0,
                    totalEpisodes=season['episode_count'],
                    vote_average=season.get('vote_average', 0)
                )

        new_media = Media(
            id=details["id"], title=details.get("title") or details.get("name"),
            year=str(details.get("release_date") or details.get("first_air_date","")).split('-')[0],
            type='series' if media_type == 'tv' else 'movie', poster_path=details.get("poster_path"),
            plot=details.get("overview"), vote_average=details.get("vote_average"),
            status=MediaStatus.PLAN_TO_WATCH, genres=details.get("genres", []),
            imdb_id=details.get("external_ids", {}).get("imdb_id"),
            tvdb_id=details.get("external_ids", {}).get("tvdb_id"), runtime=details.get("runtime"),
            episode_run_time=details.get("episode_run_time"),
            number_of_seasons=details.get("number_of_seasons"),
            production_status=details.get("status"),
            seasons=seasons_data
        )
        if self.data_manager.add_media(new_media):
            print(f"Successfully added '{new_media.title}' to the list.")
            if tmdb_id in self.displayed_cards:
                card = self.displayed_cards[tmdb_id]
                card.add_button.setText("✓ Added")
                card.add_button.setEnabled(False)
        else:
             print(f"Could not add '{new_media.title}' (already in list).")

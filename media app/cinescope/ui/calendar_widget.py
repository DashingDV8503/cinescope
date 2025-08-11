from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from cinescope.core.data_manager import DataManager
from cinescope.core.api.tvmaze_client import TVMazeClient
from cinescope.core.media import MediaStatus
import datetime

class CalendarWidget(QWidget):
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.tvmaze_client = TVMazeClient()

        layout = QVBoxLayout(self)
        self.upcoming_episodes_layout = QVBoxLayout()
        layout.addLayout(self.upcoming_episodes_layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_calendar()

    def update_calendar(self):
        self._clear_layout(self.upcoming_episodes_layout)
        upcoming_episodes = self._get_upcoming_episodes()
        for episode in upcoming_episodes:
            label = QLabel(f"{episode['showTitle']} - {episode['seasonNumber']}x{episode['episodeNumber']} \"{episode['episodeName']}\" airs on {episode['airDate']}")
            self.upcoming_episodes_layout.addWidget(label)

    def _get_upcoming_episodes(self):
        media_list = self.data_manager.get_list()
        series_to_check = [media for media in media_list if media.type == 'series' and media.status in [MediaStatus.WATCHING, MediaStatus.PLAN_TO_WATCH]]
        
        all_upcoming = []
        for series in series_to_check:
            search_results = self.tvmaze_client.search_shows(series.title)
            if search_results:
                show_id = search_results[0]['show']['id']
                show_info = self.tvmaze_client.get_show_episodes(show_id)
                if show_info and '_embedded' in show_info and 'episodes' in show_info['_embedded']:
                    today = datetime.date.today()
                    for episode in show_info['_embedded']['episodes']:
                        airdate = datetime.datetime.fromisoformat(episode['airstamp']).date()
                        if airdate >= today:
                            all_upcoming.append({
                                'showId': show_id,
                                'showTitle': series.title,
                                'airDate': airdate.isoformat(),
                                'episodeName': episode['name'],
                                'episodeNumber': episode['number'],
                                'seasonNumber': episode['season'],
                                'episodeOverview': episode.get('summary', '')
                            })
        
        all_upcoming.sort(key=lambda x: x['airDate'])
        return all_upcoming

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

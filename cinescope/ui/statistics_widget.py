from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from cinescope.core.data_manager import DataManager
from cinescope.core.media import MediaStatus

class StatisticsWidget(QWidget):
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager

        layout = QVBoxLayout(self)

        self.total_watch_time_label = QLabel()
        self.completed_movies_label = QLabel()
        self.completed_shows_label = QLabel()
        self.total_items_label = QLabel()
        self.genre_breakdown_label = QLabel()

        layout.addWidget(self.total_watch_time_label)
        layout.addWidget(self.completed_movies_label)
        layout.addWidget(self.completed_shows_label)
        layout.addWidget(self.total_items_label)
        layout.addWidget(self.genre_breakdown_label)

        self.update_stats()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_stats()

    def update_stats(self):
        stats = self._calculate_stats()
        self.total_watch_time_label.setText(f"Total Watch Time: {stats['total_watch_time']}")
        self.completed_movies_label.setText(f"Completed Movies: {stats['completed_movies']}")
        self.completed_shows_label.setText(f"Completed Shows: {stats['completed_shows']}")
        self.total_items_label.setText(f"Total Items: {stats['total_items']}")
        self.genre_breakdown_label.setText(f"Genre Breakdown:\n{stats['genre_breakdown']}")

    def _calculate_stats(self):
        media_list = self.data_manager.get_list()
        total_watch_time_minutes = 0
        completed_movies = 0
        completed_shows = 0
        total_items = len(media_list)
        genre_counts = {}

        for media in media_list:
            if media.status in [MediaStatus.WATCHING, MediaStatus.COMPLETED]:
                if media.type == 'movie' and media.runtime:
                    total_watch_time_minutes += media.runtime
                elif media.type == 'series' and media.episode_run_time:
                    if media.status == MediaStatus.COMPLETED:
                        total_episodes = sum(season.totalEpisodes for season in media.seasons.values())
                        total_watch_time_minutes += total_episodes * media.episode_run_time[0]
                    else: # Watching
                        watched_episodes = sum(season.episodesWatched for season in media.seasons.values())
                        total_watch_time_minutes += watched_episodes * media.episode_run_time[0]

            if media.status == MediaStatus.COMPLETED:
                if media.type == 'movie':
                    completed_movies += 1
                else:
                    completed_shows += 1

            for genre in media.genres:
                genre_name = genre['name']
                genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1

        # Format watch time
        days = total_watch_time_minutes // (24 * 60)
        hours = (total_watch_time_minutes % (24 * 60)) // 60
        minutes = total_watch_time_minutes % 60
        total_watch_time = f"{days}d {hours}h {minutes}m"

        # Format genre breakdown
        sorted_genres = sorted(genre_counts.items(), key=lambda item: item[1], reverse=True)
        genre_breakdown = "\n".join([f"{genre}: {count}" for genre, count in sorted_genres])

        return {
            'total_watch_time': total_watch_time,
            'completed_movies': completed_movies,
            'completed_shows': completed_shows,
            'total_items': total_items,
            'genre_breakdown': genre_breakdown
        }

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QGroupBox, QCheckBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Signal
from cinescope.core.media import Media, MediaStatus
from cinescope.ui.widgets import PosterLoader

from cinescope.core.data_manager import DataManager

class MediaDetailsWidget(QWidget):
    back_requested = Signal()

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.media = None

        main_layout = QVBoxLayout(self)

        self.back_button = QPushButton("<- Back")
        self.back_button.clicked.connect(self.back_requested.emit)
        main_layout.addWidget(self.back_button)

        details_layout = QHBoxLayout()
        self.poster_label = QLabel()
        details_layout.addWidget(self.poster_label)

        info_layout = QVBoxLayout()
        self.title_label = QLabel()
        info_layout.addWidget(self.title_label)

        self.plot_label = QLabel()
        self.plot_label.setWordWrap(True)
        info_layout.addWidget(self.plot_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems([status.value for status in MediaStatus])
        info_layout.addWidget(self.status_combo)

        details_layout.addLayout(info_layout)
        main_layout.addLayout(details_layout)

        self.progress_groupbox = QGroupBox("Progress")
        self.progress_groupbox.setCheckable(True)
        self.progress_groupbox.setChecked(False)
        main_layout.addWidget(self.progress_groupbox)

        progress_layout = QVBoxLayout(self.progress_groupbox)
        self.seasons_layout = QVBoxLayout()
        progress_layout.addLayout(self.seasons_layout)

        self.save_progress_button = QPushButton("Save Progress")
        self.save_progress_button.clicked.connect(self._save_progress)
        progress_layout.addWidget(self.save_progress_button)

        self.status_combo.currentTextChanged.connect(self._on_status_changed)

    def set_media(self, media: Media):
        self.media = media
        self.title_label.setText(f"{media.title} ({media.year})")
        self.plot_label.setText(media.plot)
        self.status_combo.setCurrentText(media.status.value)

        if media.type == 'series':
            self.progress_groupbox.setVisible(True)
            self._update_progress_view()
        else:
            self.progress_groupbox.setVisible(False)

        if media.poster_path:
            url = f"https://image.tmdb.org/t/p/w200{media.poster_path}"
            worker = PosterLoader(url)
            worker.signals.finished.connect(self._on_poster_loaded)
            worker.signals.error.connect(self._on_poster_error)
            from PySide6.QtCore import QThreadPool
            QThreadPool.globalInstance().start(worker)

    def _update_progress_view(self):
        # Clear the old season widgets
        for i in reversed(range(self.seasons_layout.count())):
            self.seasons_layout.itemAt(i).widget().setParent(None)

        if self.media and self.media.seasons:
            for season_number, season_progress in self.media.seasons.items():
                season_widget = self._create_season_widget(season_number, season_progress)
                self.seasons_layout.addWidget(season_widget)

    def _create_season_widget(self, season_number, season_progress):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        label = QLabel(f"Season {season_number}: {season_progress.episodesWatched} / {season_progress.totalEpisodes}")
        layout.addWidget(label)

        inc_button = QPushButton("+")
        inc_button.clicked.connect(lambda: self._increment_season(season_number))
        dec_button = QPushButton("-")
        dec_button.clicked.connect(lambda: self._decrement_season(season_number))
        checkbox = QCheckBox("Watched")
        checkbox.setChecked(season_progress.episodesWatched == season_progress.totalEpisodes)
        checkbox.toggled.connect(lambda checked: self._toggle_season_watched(season_number, checked))

        layout.addWidget(dec_button)
        layout.addWidget(inc_button)
        layout.addWidget(checkbox)

        return widget

    def _increment_season(self, season_number):
        if self.media and self.media.seasons:
            season = self.media.seasons[season_number]
            if season.episodesWatched < season.totalEpisodes:
                season.episodesWatched += 1
                self._update_progress_view()

    def _decrement_season(self, season_number):
        if self.media and self.media.seasons:
            season = self.media.seasons[season_number]
            if season.episodesWatched > 0:
                season.episodesWatched -= 1
                self._update_progress_view()

    def _toggle_season_watched(self, season_number, checked):
        if self.media and self.media.seasons:
            season = self.media.seasons[season_number]
            if checked:
                season.episodesWatched = season.totalEpisodes
            else:
                season.episodesWatched = 0
            self._update_progress_view()

    def _save_progress(self):
        if self.media and self.media.seasons:
            self.data_manager.update_media_seasons(self.media.id, self.media.seasons)

    def _on_poster_loaded(self, image_data: bytes):
        from PySide6.QtGui import QImage
        image = QImage()
        image.loadFromData(image_data)
        pixmap = QPixmap(image)
        self.poster_label.setPixmap(pixmap)

    def _on_poster_error(self, error_msg: str):
        print(f"Poster load failed: {error_msg}")
        self.poster_label.setText("No Image")

    def _on_status_changed(self, status_text: str):
        if self.media:
            new_status = MediaStatus(status_text)
            self.data_manager.update_media_status(self.media.id, new_status)

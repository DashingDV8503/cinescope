from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QHBoxLayout, QComboBox, QLineEdit, QLabel
from PySide6.QtCore import Signal
from cinescope.core.data_manager import DataManager
from cinescope.core.media import MediaStatus
from cinescope.ui.widgets import MediaCard

class MyListWidget(QWidget):
    media_clicked = Signal(dict)

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.data_manager.list_updated.connect(self.load_my_list)

        layout = QVBoxLayout(self)

        controls_layout = QHBoxLayout()
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Grid View", "List View"])
        controls_layout.addWidget(self.view_combo)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All Statuses")
        self.status_filter_combo.addItems([status.value for status in MediaStatus])
        controls_layout.addWidget(self.status_filter_combo)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filter by title...")
        controls_layout.addWidget(self.search_bar)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Title (A-Z)", "Title (Z-A)", "Year (Newest)", "Year (Oldest)", "Rating (Highest)", "Rating (Lowest)"])
        controls_layout.addWidget(self.sort_combo)

        layout.addLayout(controls_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.results_container = QWidget()
        self.results_grid = QGridLayout()
        self.results_container.setLayout(self.results_grid)
        scroll_area.setWidget(self.results_container)

        self._setup_connections()
        self.load_my_list()

    def _setup_connections(self):
        self.view_combo.currentTextChanged.connect(self._update_view)
        self.status_filter_combo.currentTextChanged.connect(self._apply_filters_and_sort)
        self.search_bar.textChanged.connect(self._apply_filters_and_sort)
        self.sort_combo.currentTextChanged.connect(self._apply_filters_and_sort)

    def _update_view(self, view_text):
        self._clear_layout(self.results_container.layout())
        if view_text == "List View":
            self.search_bar.setVisible(False)
            self.status_filter_combo.setVisible(False)
            self.sort_combo.setVisible(False)
            self._display_list_view()
        else:
            self.search_bar.setVisible(True)
            self.status_filter_combo.setVisible(True)
            self.sort_combo.setVisible(True)
            self.results_grid = QGridLayout(self.results_container)
            self.results_container.setLayout(self.results_grid)
            self._apply_filters_and_sort()

    def load_my_list(self):
        self._apply_filters_and_sort()

    def _apply_filters_and_sort(self):
        media_list = self.data_manager.get_list()

        # Filter by status
        status_filter = self.status_filter_combo.currentText()
        if status_filter != "All Statuses":
            media_list = [media for media in media_list if media.status.value == status_filter]

        # Filter by search term
        search_term = self.search_bar.text().lower()
        if search_term:
            media_list = [media for media in media_list if search_term in media.title.lower()]

        # Sort
        sort_option = self.sort_combo.currentText()
        if sort_option == "Title (A-Z)":
            media_list.sort(key=lambda x: x.title)
        elif sort_option == "Title (Z-A)":
            media_list.sort(key=lambda x: x.title, reverse=True)
        elif sort_option == "Year (Newest)":
            media_list.sort(key=lambda x: x.year, reverse=True)
        elif sort_option == "Year (Oldest)":
            media_list.sort(key=lambda x: x.year)
        elif sort_option == "Rating (Highest)":
            media_list.sort(key=lambda x: x.vote_average, reverse=True)
        elif sort_option == "Rating (Lowest)":
            media_list.sort(key=lambda x: x.vote_average)

        self._display_grid_view(media_list)

    def _display_grid_view(self, media_list):
        self._clear_layout(self.results_grid)
        row, col = 0, 0
        for media in media_list:
            media_dict = media.__dict__
            if media.type == 'series' and 'name' not in media_dict:
                media_dict['name'] = media.title
            card = MediaCard(media_dict, is_added=True)
            card.media_clicked.connect(self.media_clicked.emit)
            self.results_grid.addWidget(card, row, col)
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def _display_list_view(self):
        media_list = self.data_manager.get_list()
        movies = [media for media in media_list if media.type == 'movie']
        series = [media for media in media_list if media.type == 'series']

        list_layout = QVBoxLayout()
        self.results_container.setLayout(list_layout)

        list_layout.addWidget(QLabel("Movies"))
        movies_scroll_area = QScrollArea()
        movies_scroll_area.setWidgetResizable(True)
        movies_widget = QWidget()
        movies_layout = QHBoxLayout(movies_widget)
        for movie in movies:
            media_dict = movie.__dict__
            card = MediaCard(media_dict, is_added=True)
            card.media_clicked.connect(self.media_clicked.emit)
            movies_layout.addWidget(card)
        movies_scroll_area.setWidget(movies_widget)
        list_layout.addWidget(movies_scroll_area)

        list_layout.addWidget(QLabel("TV Shows"))
        series_scroll_area = QScrollArea()
        series_scroll_area.setWidgetResizable(True)
        series_widget = QWidget()
        series_layout = QHBoxLayout(series_widget)
        for show in series:
            media_dict = show.__dict__
            if 'name' not in media_dict:
                media_dict['name'] = show.title
            card = MediaCard(media_dict, is_added=True)
            card.media_clicked.connect(self.media_clicked.emit)
            series_layout.addWidget(card)
        series_scroll_area.setWidget(series_widget)
        list_layout.addWidget(series_scroll_area)

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

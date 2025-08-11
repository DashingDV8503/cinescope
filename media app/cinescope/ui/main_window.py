import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QStackedWidget, QToolBar
from PySide6.QtGui import QAction
from cinescope.core.data_manager import DataManager
from cinescope.ui.my_list_widget import MyListWidget
from cinescope.ui.search_widget import SearchWidget
from cinescope.ui.media_details_widget import MediaDetailsWidget
from cinescope.ui.statistics_widget import StatisticsWidget
from cinescope.ui.calendar_widget import CalendarWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.setWindowTitle("CineScope")
        self.resize(1000, 800)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.my_list_widget = MyListWidget(self.data_manager)
        self.search_widget = SearchWidget(self.data_manager)
        self.media_details_widget = MediaDetailsWidget(self.data_manager)
        self.statistics_widget = StatisticsWidget(self.data_manager)
        self.calendar_widget = CalendarWidget(self.data_manager)

        self.stacked_widget.addWidget(self.my_list_widget)
        self.stacked_widget.addWidget(self.search_widget)
        self.stacked_widget.addWidget(self.media_details_widget)
        self.stacked_widget.addWidget(self.statistics_widget)
        self.stacked_widget.addWidget(self.calendar_widget)

        self.my_list_widget.media_clicked.connect(self.show_media_details)
        self.media_details_widget.back_requested.connect(lambda: self.stacked_widget.setCurrentWidget(self.my_list_widget))

        self.create_toolbar()

    def show_media_details(self, media_info):
        media = self.data_manager.get_media_by_id(media_info['id'])
        if media:
            self.media_details_widget.set_media(media)
            self.stacked_widget.setCurrentWidget(self.media_details_widget)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        my_list_action = QAction("My List", self)
        my_list_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.my_list_widget))
        toolbar.addAction(my_list_action)

        search_action = QAction("Search", self)
        search_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.search_widget))
        toolbar.addAction(search_action)

        stats_action = QAction("Statistics", self)
        stats_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.statistics_widget))
        toolbar.addAction(stats_action)

        calendar_action = QAction("Calendar", self)
        calendar_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.calendar_widget))
        toolbar.addAction(calendar_action)
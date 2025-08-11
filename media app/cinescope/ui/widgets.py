
import requests
from PySide6.QtCore import Qt, Signal, QObject, QRunnable, QThreadPool
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

# --- Worker for Background Tasks ---
class WorkerSignals(QObject):
    """Defines signals available from a running worker thread."""
    finished = Signal(bytes)
    error = Signal(str)

class PosterLoader(QRunnable):
    """Worker thread for loading an image from a URL."""
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.signals = WorkerSignals()

    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            self.signals.finished.emit(response.content)
        except requests.RequestException as e:
            self.signals.error.emit(str(e))

# --- MediaCard ---
class MediaCard(QWidget):
    add_media_requested = Signal(dict)
    media_clicked = Signal(dict)

    def __init__(self, media_result: dict, is_added: bool):
        super().__init__()
        self.media_info = media_result
        self.setFixedSize(160, 300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.poster_label = QLabel("Loading...")
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setFixedSize(160, 240)
        self.poster_label.setStyleSheet("background-color: #333; color: white;")
        title = self.media_info.get("title") or self.media_info.get("name")
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        
        if not is_added:
            self.add_button = QPushButton("Add to List")
            self.add_button.clicked.connect(self._on_add_clicked)
        else:
            self.add_button = QPushButton("View Details")
            self.add_button.clicked.connect(self._on_view_details_clicked)

        layout.addWidget(self.poster_label)
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self.add_button)
        self._load_poster(self.media_info.get("poster_path"))
    
    def mousePressEvent(self, event):
        self.media_clicked.emit(self.media_info)
        super().mousePressEvent(event)
    
    def _load_poster(self, poster_path):
        if not poster_path:
            self.poster_label.setText("No Image")
            return
        url = f"https://image.tmdb.org/t/p/w200{poster_path}"
        worker = PosterLoader(url)
        worker.signals.finished.connect(self._on_poster_loaded)
        worker.signals.error.connect(self._on_poster_error)
        QThreadPool.globalInstance().start(worker)

    def _on_poster_loaded(self, image_data: bytes):
        image = QImage()
        image.loadFromData(image_data)
        pixmap = QPixmap(image)
        self.poster_label.setPixmap(pixmap.scaled(self.poster_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _on_poster_error(self, error_msg: str):
        print(f"Poster load failed: {error_msg}")
        self.poster_label.setText("Load Failed")

    def _on_view_details_clicked(self):
        self.media_clicked.emit(self.media_info)

    def _on_add_clicked(self):
        self.add_button.setText("Adding...")
        self.add_button.setEnabled(False)
        self.add_media_requested.emit(self.media_info)

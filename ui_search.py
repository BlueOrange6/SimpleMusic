from PyQt6.QtWidgets import QWidget, QLineEdit, QFrame, QGraphicsOpacityEffect
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QPropertyAnimation, QPoint, QEasingCurve, QRect, QEvent
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtSvgWidgets import QSvgWidget 
from library import find_song
from downloader import download_song
from helpers import resource_path  # <--- IMPORT HELPER

class DownloadWorker(QThread):
    finished = pyqtSignal(str, str)
    def __init__(self, query):
        super().__init__()
        self.query = query
    def run(self):
        path, title = download_song(self.query)
        self.finished.emit(path if path else "", title if title else self.query)

class SearchWindow(QWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.is_hiding = False

        self.setFixedSize(400, 60)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 400, 60)
        self.main_frame.setStyleSheet("QFrame { background-color: #1a1a1a; border: 2px solid #333; border-radius: 30px; }")

        # [FIX] Use resource_path for icons
        self.search_icon = QSvgWidget(resource_path("assets/search.svg"), self.main_frame)
        self.search_icon.setGeometry(18, 18, 24, 24)
        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.5)
        self.search_icon.setGraphicsEffect(op)

        self.input = QLineEdit(self.main_frame)
        self.input.setPlaceholderText("Search or type !command...")
        self.input.setGeometry(55, 0, 330, 60)
        self.input.setStyleSheet("QLineEdit { color: white; background: transparent; border: none; font-size: 15px; }")
        self.input.returnPressed.connect(self.handle_search)

        # [FIX] Use resource_path for icons
        self.dl_icon = QSvgWidget(resource_path("assets/download.svg"), self.main_frame)
        self.dl_icon.setGeometry(18, 18, 24, 24)
        self.dl_opacity = QGraphicsOpacityEffect(self)
        self.dl_opacity.setOpacity(0.2)
        self.dl_icon.setGraphicsEffect(self.dl_opacity)
        self.dl_icon.hide()

        self.setup_animations()

    def setup_animations(self):
        self.pulse_anim = QPropertyAnimation(self.dl_opacity, b"opacity")
        self.pulse_anim.setDuration(1400)
        self.pulse_anim.setLoopCount(-1)
        self.pulse_anim.setKeyValueAt(0, 0.2)
        self.pulse_anim.setKeyValueAt(0.5, 1.0)
        self.pulse_anim.setKeyValueAt(1, 0.2)

        self.morph_anim = QPropertyAnimation(self.main_frame, b"geometry")
        self.morph_anim.setDuration(450)
        self.morph_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(350)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.slide_anim.finished.connect(self._on_animation_finished)

    def handle_search(self):
        query = self.input.text().strip()
        if not query: return
        
        if query.startswith("!"):
            self.player.process_command(query)
            self.input.clear()
            return
        
        existing = find_song(query)
        if existing:
            self.hide_animated()
            self.player.play_user_search(str(existing.absolute()), existing.stem.replace('_', ' ')) 
        else:
            self.enter_download_mode()
            self.worker = DownloadWorker(query)
            self.worker.finished.connect(self.on_download_finished)
            self.worker.start()

    def show_search(self):
        if self.isVisible() and not self.is_hiding:
            self.hide_animated()
            return

        self.pulse_anim.stop()
        self.dl_icon.hide()
        self.search_icon.show()
        self.input.show()
        self.main_frame.setGeometry(0, 0, 400, 60)
        self.input.clear()
        self.is_hiding = False

        screen = QGuiApplication.primaryScreen().geometry()
        x_pos = (screen.width() - 400) // 2
        self.move(x_pos, -60)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()
        
        self.slide_anim.setStartValue(QPoint(x_pos, -60))
        self.slide_anim.setEndValue(QPoint(x_pos, 50))
        self.slide_anim.start()

    def enter_download_mode(self):
        self.input.hide()
        self.search_icon.hide()
        self.morph_anim.setStartValue(QRect(0, 0, 400, 60))
        self.morph_anim.setEndValue(QRect(170, 0, 60, 60))
        self.morph_anim.start()
        
        self.dl_icon.show()
        self.pulse_anim.start()

    def on_download_finished(self, song_path, display_name):
        self.pulse_anim.stop()
        if song_path: 
            self.player.play_user_search(song_path, display_name)
        self.hide_animated()

    def hide_animated(self):
        if self.is_hiding: return
        self.is_hiding = True
        self.slide_anim.setStartValue(self.pos())
        self.slide_anim.setEndValue(QPoint(self.x(), -60))
        self.slide_anim.start()

    def _on_animation_finished(self):
        if self.is_hiding: 
            self.hide()
            self.is_hiding = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_animated()
        else:
            super().keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            if self.isVisible() and not self.is_hiding: 
                self.hide_animated()
        super().changeEvent(event)
import vlc
from PyQt6.QtWidgets import (QWidget, QPushButton, QLabel, QSlider, QHBoxLayout, QVBoxLayout, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect, QEvent
from PyQt6.QtGui import QFontMetrics, QPainter, QGuiApplication, QColor
from PyQt6.QtSvgWidgets import QSvgWidget
from helpers import resource_path  # <--- Ensure helpers.py is in the folder

class ScrollingLabel(QWidget):
    """
    Optimized for 60 FPS smooth scrolling.
    """
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text
        self.pos_x = 0.0 # Use float for precision
        self.scroll_speed = 0.8 # Pixels per frame (at 60fps)
        self.spacing = 80 # Space between repeating text
        
        # 60 FPS Timer (approx 16ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scroll)
        self.timer.start(16) 

    def set_text(self, text):
        if self.text == text: return
        self.text = text
        self.pos_x = 0.0
        self.update()

    def update_scroll(self):
        if not self.isVisible() or not self.text: return
        
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(self.text)
        
        if text_width > self.width():
            self.pos_x -= self.scroll_speed
            # Reset when text has fully scrolled plus spacing
            if self.pos_x < -(text_width + self.spacing): 
                self.pos_x = 0.0
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Enable Antialiasing for smoother text edges during movement
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(self.text)
        
        # Draw white text
        painter.setPen(Qt.GlobalColor.white)
        
        # Center vertically
        y = (self.height() + metrics.ascent() - metrics.descent()) / 2
        
        if text_width <= self.width():
            # If text fits, just center it statically
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text)
        else:
            # Draw text twice to create seamless infinite loop
            painter.drawText(QPoint(int(self.pos_x), int(y)), self.text)
            painter.drawText(QPoint(int(self.pos_x + text_width + self.spacing), int(y)), self.text)

class VolumeBar(QWidget):
    """Popup volume slider."""
    def __init__(self, player, parent_win):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.player = player
        self.parent_win = parent_win
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 30)
        
        self.frame = QFrame(self)
        self.frame.setGeometry(0, 0, 320, 30)
        self.frame.setStyleSheet("QFrame { background-color: #1a1a1a; border: 1px solid #333; border-radius: 15px; }")
        
        layout = QHBoxLayout(self.frame)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # Icon
        self.icon = QSvgWidget(resource_path("assets/volume.svg"))
        self.icon.setFixedSize(16, 16)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(self.player.get_volume())
        
        # [FIX] Enhanced Slider Styling
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #333;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: white;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 10px;
                height: 10px;
                margin: -3px 0; /* Centers handle on groove */
                border-radius: 5px;
            }
            QSlider::handle:horizontal:hover {
                background: #e0e0e0;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)
        
        self.slider.valueChanged.connect(self.player.set_volume)
        self.player.volume_changed.connect(self.sync_slider)
        
        layout.addWidget(self.icon)
        layout.addWidget(self.slider)
        
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def sync_slider(self, val):
        self.slider.blockSignals(True)
        self.slider.setValue(val)
        self.slider.blockSignals(False)

    def slide_show(self):
        try: self.anim.finished.disconnect(self.hide)
        except: pass
        
        p = self.parent_win.pos()
        target_x = p.x() + (460 - 320) // 2
        target_y = p.y() - 40 
        
        self.setGeometry(QRect(target_x, p.y() + 10, 320, 30))
        self.show()
        self.lower() 
        self.parent_win.raise_()
        self.activateWindow()
        
        self.anim.setEndValue(QRect(target_x, target_y, 320, 30))
        self.anim.start()

    def slide_hide(self):
        if not self.isVisible(): return
        try: self.anim.finished.disconnect(self.hide)
        except: pass
        
        self.anim.finished.connect(self.hide)
        self.anim.setEndValue(QRect(self.x(), self.parent_win.y() + 10, 320, 30))
        self.anim.start()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow() and self.isVisible():
            self.slide_hide()
        super().changeEvent(event)

class PlayerWindow(QWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.current_play_icon = "assets/play.svg"
        
        self.setFixedSize(460, 80)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.vol_bar = VolumeBar(self.player, self)
        self.vol_bar.hide()
        
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 460, 80)
        self.main_frame.setStyleSheet("QFrame { background-color: #1a1a1a; border: 2px solid #333; border-radius: 40px; }")
        
        layout = QHBoxLayout(self.main_frame)
        layout.setContentsMargins(15, 12, 25, 12)
        
        # Controls
        self.controls = QHBoxLayout()
        self.controls.setSpacing(10)
        
        self.btn_b, _ = self.create_btn(resource_path("assets/skip_back.svg"), 25, 50)
        self.btn_b.clicked.connect(self.player.skip_back)
        
        self.play_btn, self.svg_p = self.create_btn(resource_path("assets/play.svg"), 28, 50)
        self.play_btn.clicked.connect(self.player.toggle)
        
        self.btn_f, _ = self.create_btn(resource_path("assets/skip_next.svg"), 25, 50)
        self.btn_f.clicked.connect(self.player.skip_next)
        
        layout.addLayout(self.controls)

        # Info
        info = QVBoxLayout()
        self.title = ScrollingLabel("Ready to play")
        self.title.setFixedHeight(22)
        
        self.prog = QSlider(Qt.Orientation.Horizontal)
        self.prog.setRange(0, 1000)
        
        # [FIX] Clean, Minimalist Slider Style
        self.prog.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #333;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: white;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 12px;
                height: 12px;
                margin: -4px 0; 
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #f0f0f0;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        
        self.prog.sliderReleased.connect(lambda: self.player.set_position(self.prog.value() / 1000))
        
        time_l = QHBoxLayout()
        self.lbl_cur = QLabel("0:00")
        self.lbl_tot = QLabel("0:00")
        for l in [self.lbl_cur, self.lbl_tot]: 
            l.setStyleSheet("color: #888; font-family: 'Segoe UI'; font-size: 10px; border: none;")
        
        time_l.addWidget(self.lbl_cur)
        time_l.addStretch()
        time_l.addWidget(self.lbl_tot)
        
        info.addWidget(self.title)
        info.addWidget(self.prog)
        info.addLayout(time_l)
        
        layout.addLayout(info)
        layout.setStretch(1, 1)

        # UI Update Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(500)
        
        self.player.song_changed.connect(self.title.set_text)
        self.player.status_message.connect(self.show_temp_message)
        
        # Window Animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(450)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_temp_message(self, msg):
        self.title.set_text(msg)
        QTimer.singleShot(2000, lambda: self.title.set_text(self.player.current_display_name))

    def create_btn(self, path, h, w):
        btn = QPushButton()
        btn.setFixedSize(w, 40)
        btn.setStyleSheet("background: transparent; border: none;")
        
        svg = QSvgWidget(path, btn)
        svg.setFixedHeight(h)
        svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        svg.adjustSize()
        svg.move((w - svg.width()) // 2, (40 - h) // 2)
        
        self.controls.addWidget(btn)
        return btn, svg

    def update_ui(self):
        st = self.player.player.get_state()
        ni = "assets/pause.svg" if st == vlc.State.Playing else "assets/play.svg"
        
        if self.current_play_icon != ni: 
            self.svg_p.load(resource_path(ni))
            self.svg_p.adjustSize()
            self.svg_p.move((50 - self.svg_p.width()) // 2, 6)
            self.current_play_icon = ni
            
        dur = self.player.get_duration()
        self.lbl_tot.setText(f"{int(dur // 60)}:{int(dur % 60):02d}")
        
        if dur > 0: 
            if not self.prog.isSliderDown():
                self.lbl_cur.setText(f"{int(self.player.get_time() // 60)}:{int(self.player.get_time() % 60):02d}")
                self.prog.setValue(int(self.player.get_position() * 1000))

    def toggle(self):
        screen = QGuiApplication.primaryScreen().geometry()
        tx = (screen.width() - 460) // 2
        ty = screen.height() - 150
        
        if self.isVisible():
            self.vol_bar.hide()
            try: self.anim.finished.disconnect()
            except: pass
            self.anim.setEndValue(QRect(tx, screen.height(), 460, 80))
            self.anim.finished.connect(self.hide)
            self.anim.start()
        else:
            try: self.anim.finished.disconnect()
            except: pass
            self.setGeometry(tx, screen.height(), 460, 80)
            self.show()
            self.raise_()
            self.activateWindow()
            self.anim.setEndValue(QRect(tx, ty, 460, 80))
            self.anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.vol_bar.slide_hide() if self.vol_bar.isVisible() else self.vol_bar.slide_show()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.player.process_command("!add favorites")
            self.main_frame.setStyleSheet("QFrame { background-color: #1a1a1a; border: 2px solid #2ecc71; border-radius: 40px; }")
            QTimer.singleShot(500, lambda: self.main_frame.setStyleSheet("QFrame { background-color: #1a1a1a; border: 2px solid #333; border-radius: 40px; }"))
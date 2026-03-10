from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, 
                             QFrame, QHBoxLayout, QGraphicsOpacityEffect, QCheckBox)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QUrl
from PyQt6.QtGui import QDesktopServices
from pathlib import Path
import sys
import winreg  # Required for Windows Registry editing
import updater

class OptionsWindow(QWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        
        self.setFixedSize(380, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Container
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 380, 500)
        self.container.setStyleSheet("""
            QFrame#Container {
                background-color: #121212;
                border: 2px solid #333;
                border-radius: 20px;
            }
            QLabel { color: white; font-family: 'Segoe UI'; }
            QCheckBox { color: #ccc; spacing: 10px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QScrollBar:vertical {
                border: none; background: #222; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #555; min-height: 20px; border-radius: 3px;
            }
        """)
        self.container.setObjectName("Container")

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("CONTROLS & SETTINGS")
        title.setStyleSheet("font-weight: bold; font-size: 14px; letter-spacing: 1px; color: #888;")
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton { color: #666; font-size: 20px; border: none; background: transparent; }
            QPushButton:hover { color: white; }
        """)
        close_btn.clicked.connect(self.hide_animated)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        self.layout.addLayout(header_layout)

        # --- ACTIONS SECTION ---
        actions_layout = QHBoxLayout()
        self.btn_folder = self.create_action_btn("📂 Music Folder")
        self.btn_folder.clicked.connect(self.open_music_folder)
        
        self.btn_update = self.create_action_btn("⚡ Update App")
        self.btn_update.clicked.connect(self.run_update)

        actions_layout.addWidget(self.btn_folder)
        actions_layout.addWidget(self.btn_update)
        self.layout.addLayout(actions_layout)

        # --- STARTUP CHECKBOX ---
        self.chk_startup = QCheckBox("Run when Windows starts")
        self.chk_startup.setChecked(self.is_startup_enabled())
        self.chk_startup.toggled.connect(self.toggle_startup)
        self.layout.addWidget(self.chk_startup)

        # --- COMMANDS LIST ---
        lbl_cmd = QLabel("COMMAND LIST")
        lbl_cmd.setStyleSheet("font-size: 11px; font-weight: bold; color: #555; margin-top: 10px;")
        self.layout.addWidget(lbl_cmd)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 10, 0)
        scroll_layout.setSpacing(12)

        commands = [
            ("!play <playlist>", "Start a specific playlist"),
            ("!shuffle", "Shuffle all songs"),
            ("!artist <name>", "Loop songs by an artist"),
            ("!add <playlist>", "Add current song to playlist"),
            ("!add <playlist> <song>", "Search & add to playlist"),
            ("!create <name>", "Create a new playlist"),
            ("!remove", "Remove current song from playlist"),
            ("!delete", "Permanently delete file"),
            ("!vol <0-100>", "Set volume"),
            ("!exit", "Close application")
        ]

        for cmd, desc in commands:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)
            c_lbl = QLabel(cmd)
            c_lbl.setStyleSheet("color: #4facfe; font-weight: bold; font-family: 'Consolas'; font-size: 13px;")
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
            row_layout.addWidget(c_lbl)
            row_layout.addWidget(d_lbl)
            scroll_layout.addWidget(row)

        scroll_layout.addStretch()
        self.scroll.setWidget(scroll_content)
        self.layout.addWidget(self.scroll)

        # Animation
        self.opacity = QGraphicsOpacityEffect(self)
        self.opacity.setOpacity(0)
        self.setGraphicsEffect(self.opacity)
        self.anim_op = QPropertyAnimation(self.opacity, b"opacity")
        self.anim_op.setDuration(250)
        self.anim_op.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def create_action_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #222; color: white; border: 1px solid #333; border-radius: 8px; font-size: 12px; }
            QPushButton:hover { background-color: #333; border: 1px solid #555; }
        """)
        return btn

    def open_music_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path("music").absolute())))

    def run_update(self):
        self.btn_update.setText("Checking...")
        if not updater.check_for_updates():
            self.btn_update.setText("Up to Date ✓")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.btn_update.setText("⚡ Update App"))

    # --- STARTUP LOGIC ---
    def is_startup_enabled(self):
        """Checks Registry for the app entry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "NeoFiMusic")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    def toggle_startup(self, checked):
        """Adds or removes the app from Windows Registry."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "NeoFiMusic"
        exe_path = sys.executable  # Points to the python.exe or the compiled .exe

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if checked:
                # Add to registry
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                # Remove from registry
                try: winreg.DeleteValue(key, app_name)
                except FileNotFoundError: pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry Error: {e}")

    def show_animated(self):
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        self.show()
        self.raise_()
        self.anim_op.setStartValue(0)
        self.anim_op.setEndValue(1)
        self.anim_op.start()

    def hide_animated(self):
        self.anim_op.setStartValue(1)
        self.anim_op.setEndValue(0)
        self.anim_op.finished.connect(self.hide)
        self.anim_op.start()
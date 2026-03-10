from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from helpers import resource_path  # <--- IMPORT HELPER

class Tray:
    def __init__(self, app, player, search_window, player_window, options_window):
        self.app = app
        self.player = player
        self.search_window = search_window
        self.player_window = player_window
        self.options_window = options_window 
        
        # [FIX] Use resource_path for the tray icon
        # This fixes the silent crash when running as .exe
        self.tray_icon = QSystemTrayIcon(QIcon(resource_path("icon.ico")), self.app)
        self.tray_icon.setToolTip("Music Player")
        
        # Create Menu
        self.menu = QMenu()
        
        # Actions
        self.action_show_search = QAction("Search", self.app)
        self.action_show_search.triggered.connect(self.search_window.show_search)
        
        self.action_show_player = QAction("Show Player", self.app)
        self.action_show_player.triggered.connect(self.player_window.toggle)

        self.action_options = QAction("Options", self.app)
        self.action_options.triggered.connect(self.options_window.show_animated)
        
        self.action_quit = QAction("Exit", self.app)
        self.action_quit.triggered.connect(self.app.quit)
        
        # Add to Menu
        self.menu.addAction(self.action_show_search)
        self.menu.addAction(self.action_show_player)
        self.menu.addSeparator()
        self.menu.addAction(self.action_options)
        self.menu.addSeparator()
        self.menu.addAction(self.action_quit)
        
        # Finalize
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
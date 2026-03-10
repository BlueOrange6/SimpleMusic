import sys
from PyQt6.QtWidgets import QApplication

# --- Import Custom Modules ---
from player import MusicPlayer
from ui_player import PlayerWindow
from ui_search import SearchWindow
from ui_options import OptionsWindow
from shortcut_listener import ShortcutListener
from tray import Tray
import updater

# 1. AUTO-UPDATE CHECK
updater.check_for_updates()

# 2. Initialize Application
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# 3. Initialize Core Logic
player = MusicPlayer()

# 4. Initialize UI Windows
search_window = SearchWindow(player)
player_window = PlayerWindow(player)
options_window = OptionsWindow(player) # Created here

# 5. Connect Internal Signals
player.show_options.connect(options_window.show_animated)

# 6. Initialize System Tray
# [FIX] Now passing 'options_window' to the tray
system_tray = Tray(app, player, search_window, player_window, options_window)

# 7. Connect Global Shortcut Listener
listener = ShortcutListener()

listener.show_search.connect(search_window.show_search)
listener.show_player.connect(player_window.toggle)
listener.play_pause.connect(player.toggle)
listener.next_track.connect(player.skip_next)
listener.prev_track.connect(player.skip_back)

listener.start()

# 8. Start Event Loop
sys.exit(app.exec())
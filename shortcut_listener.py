import ctypes
import pynput
from ctypes import wintypes
from PyQt6.QtCore import QThread, pyqtSignal

user32 = ctypes.WinDLL('user32', use_last_error=True)

class ShortcutListener(QThread):
    # Signals for Main App
    show_search = pyqtSignal()
    show_player = pyqtSignal()
    play_pause = pyqtSignal()
    next_track = pyqtSignal()
    prev_track = pyqtSignal()

    def run(self):
        """
        Runs in a background thread.
        1. Registers global Windows hotkeys (Ctrl+Alt+S/P).
        2. Starts a pynput listener for Media Keys.
        3. Enters Windows Message Loop to catch hotkey events.
        """
        
        # 1. Native Windows Hotkeys
        # IDs must be unique
        self.hotkey_ids = {
            1: (0x0002 | 0x0001, 0x53), # Ctrl (0x02) + Alt (0x01) + S (0x53)
            2: (0x0002 | 0x0001, 0x50), # Ctrl (0x02) + Alt (0x01) + P (0x50)
        }

        for hk_id, (mods, vk) in self.hotkey_ids.items():
            if not user32.RegisterHotKey(None, hk_id, mods, vk):
                print(f"Failed to register hotkey ID {hk_id}")

        # 2. Pynput for Hardware Media Keys
        # We start this listener inside this thread
        self.media_listener = pynput.keyboard.Listener(on_press=self.on_media_press)
        self.media_listener.start()

        # 3. Windows Message Loop (Blocking)
        try:
            msg = wintypes.MSG()
            # GetMessageW waits for a message (blocks the thread efficiently)
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312: # WM_HOTKEY message
                    if msg.wParam == 1: 
                        self.show_search.emit()
                    elif msg.wParam == 2: 
                        self.show_player.emit()
                
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            self.stop()

    def on_media_press(self, key):
        """Callback for pynput."""
        try:
            if key == pynput.keyboard.Key.media_play_pause:
                self.play_pause.emit()
            elif key == pynput.keyboard.Key.media_next:
                self.next_track.emit()
            elif key == pynput.keyboard.Key.media_previous:
                self.prev_track.emit()
        except AttributeError:
            pass

    def stop(self):
        """Clean up hotkeys."""
        if hasattr(self, 'media_listener'):
            self.media_listener.stop()
        
        for hk_id in self.hotkey_ids.keys():
            user32.UnregisterHotKey(None, hk_id)
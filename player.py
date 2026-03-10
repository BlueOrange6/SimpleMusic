import vlc
import os
import json
import random
import sys
import re
from pathlib import Path
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication

# --- Safe Data Path Logic ---
def get_app_dir():
    """Gets the folder where the script OR the .exe is located."""
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        return Path(sys.executable).parent.absolute()
    else:
        # Running as a Python script
        return Path(__file__).parent.absolute()

BASE_DIR = get_app_dir()

# These will now safely generate right next to your .exe
MUSIC_DIR = BASE_DIR / "music"
MUSIC_DIR.mkdir(exist_ok=True)

SETTINGS_FILE = BASE_DIR / "settings.json"
PLAYLIST_FILE = BASE_DIR / "playlists.json"

class MusicPlayer(QObject): 
    # Signals to communicate with UI
    song_changed = pyqtSignal(str) 
    volume_changed = pyqtSignal(int)
    status_message = pyqtSignal(str)
    show_options = pyqtSignal() # Signal to open Options Window

    def __init__(self):
        super().__init__()
        # VLC Setup
        self.instance = vlc.Instance("--quiet")
        self.player = self.instance.media_player_new()
        
        # Load Data
        self.current_volume = self.load_volume()
        self.player.audio_set_volume(self.current_volume)
        self.playlists = self.load_all_playlists()
        
        # State Variables
        self.current_display_name = "Ready"
        self.current_path = None
        
        # --- History Stacks ---
        self.history = []           # Back button stack
        self.forward_history = []   # Forward button stack
        
        # --- Queue & Deck System ---
        self.global_queue = []          # The "Deck" (All songs shuffled)
        self.queue = []                 # The "Playlist" (User custom queue)
        self.is_queue_mode = False      # True = Playing Playlist, False = Playing Global Deck
        self.current_playlist_name = None 
        
        # Playback Monitor
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_playback_status)
        self.monitor_timer.start(1000)

    # --- Loading & Saving ---
    def load_volume(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f: return json.load(f).get("volume", 50)
            except: return 50
        return 50

    def load_all_playlists(self):
        if PLAYLIST_FILE.exists():
            try:
                with open(PLAYLIST_FILE, "r") as f: return json.load(f)
            except: return {"favorites": []}
        return {"favorites": []}

    def save_playlists(self):
        try:
            # Save everything except temporary artist loops (starting with _)
            to_save = {k: v for k, v in self.playlists.items() if not k.startswith("_")}
            with open(PLAYLIST_FILE, "w") as f:
                json.dump(to_save, f, indent=4)
        except Exception as e:
            print(f"Error saving playlists: {e}")

    # --- HELPER: Smart Song Search ---
    def _find_song_by_query(self, query):
        """Searches for a song path using robust fuzzy matching."""
        query_compressed = re.sub(r'\W+', '', query).lower()
        valid_exts = {'.mp3', '.wav', '.flac', '.m4a', '.opus', '.webm', '.ogg'}
        
        for f in MUSIC_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in valid_exts:
                # 1. Replace underscores with spaces for readability
                fname = f.stem.lower().replace("_", " ")
                # 2. Compress filename (remove spaces/symbols)
                fname_compressed = re.sub(r'\W+', '', fname)
                
                # 3. Check if query is inside the filename
                if query_compressed in fname_compressed:
                    return str(f.absolute())
        return None

    # --- HELPER: Add to Playlist ---
    def _add_path_to_playlist(self, playlist_name, path):
        """Adds a path to a playlist safely and saves."""
        if playlist_name not in self.playlists: 
            self.playlists[playlist_name] = []
        
        if path not in self.playlists[playlist_name]:
            self.playlists[playlist_name].append(path)
            self.save_playlists()
            self.status_message.emit(f"Added to {playlist_name}")
            
            # Real-time update: If playing this playlist, add to live queue
            if self.is_queue_mode and self.current_playlist_name == playlist_name:
                self.queue.append(path)
        else:
            self.status_message.emit(f"Already in {playlist_name}")

    # --- QUEUE MANAGEMENT (The "Deck") ---
    def ensure_global_queue(self):
        """If the global deck is empty, refill and reshuffle."""
        if not self.global_queue:
            print("DEBUG: Reshuffling Global Library...")
            valid_exts = {'.mp3', '.wav', '.flac', '.m4a', '.opus', '.webm', '.ogg'}
            songs = [
                str(f.absolute()) for f in MUSIC_DIR.iterdir() 
                if f.is_file() and f.suffix.lower() in valid_exts
            ]
            if songs:
                random.shuffle(songs)
                self.global_queue = songs
            else:
                print("DEBUG: Library is empty.")

    # --- SMART PLAY (User Click from Search) ---
    def play_user_search(self, path, title=None):
        clean_path = self._clean_path(path)
        self.forward_history = [] # Manual play wipes forward history

        # 1. Exit playlist mode if song is not in current playlist
        if self.is_queue_mode and self.current_playlist_name:
            playlist_songs = self.playlists.get(self.current_playlist_name, [])
            if clean_path not in playlist_songs:
                self.is_queue_mode = False
                self.queue = []
                self.current_playlist_name = None
                self.status_message.emit("Exited Playlist")
        
        # 2. Remove this song from the global deck (prevent repeats)
        if clean_path in self.global_queue:
            self.global_queue.remove(clean_path)

        self.load_and_play(clean_path, title)

    # --- NAVIGATION LOGIC ---
    def skip_next(self):
        # Priority 1: Forward History (Redo button)
        if self.forward_history:
            mrl, title = self.forward_history.pop()
            self.load_and_play(mrl, title)
            return

        # Priority 2: Playlist Mode
        if self.is_queue_mode:
            if not self.queue:
                # Loop playlist if empty
                if self.current_playlist_name in self.playlists:
                    self.queue = list(self.playlists[self.current_playlist_name])
                    random.shuffle(self.queue)
                else:
                    self.status_message.emit("Playlist Empty")
                    self.is_queue_mode = False
            
            if self.queue:
                next_song = self.queue.pop(0)
                self.load_and_play(next_song)
                return

        # Priority 3: Global Deck
        self.ensure_global_queue()
        if not self.global_queue:
            self.status_message.emit("No Songs Found")
            return

        target = self.global_queue.pop(0)
        
        # Skip deleted files automatically
        if not os.path.exists(target):
            self.skip_next()
            return
            
        self.load_and_play(target)

    def skip_back(self):
        if self.history:
            # Put current song back on top of the deck/queue
            # This ensures if you hit "Next" again, you get the same song
            if self.current_path:
                if self.is_queue_mode:
                    self.queue.insert(0, self.current_path)
                else:
                    self.global_queue.insert(0, self.current_path)

            path, title = self.history.pop()
            
            # Re-play logic (bypassing history stack add)
            self.player.stop()
            clean_path = self._clean_path(path)
            self.current_path = clean_path
            
            media = self.instance.media_new_path(clean_path)
            self.player.set_media(media)
            self.current_display_name = title
            self.player.play()
            self.song_changed.emit(self.current_display_name)
        else:
            self.status_message.emit("No history")

    def load_and_play(self, path, title=None):
        """Standard Play: Adds to History Stack."""
        if self.player.get_media():
            mrl = self.player.get_media().get_mrl()
            current_title = self.current_display_name
            # Prevent duplicate history entries
            if not self.history or self.history[-1][0] != mrl:
                self.history.append((mrl, current_title))
                if len(self.history) > 50: self.history.pop(0)
        
        self._play_now(path, title)

    def _play_now(self, path, title):
        """Internal VLC Trigger."""
        self.player.stop()
        clean_path = self._clean_path(path)
        
        if not os.path.exists(clean_path):
            if self.is_queue_mode: self.skip_next()
            return

        self.current_path = clean_path
        media = self.instance.media_new_path(clean_path)
        self.player.set_media(media)
        self.current_display_name = title or Path(clean_path).stem.replace('_', ' ')
        self.player.play()
        self.song_changed.emit(self.current_display_name)

    def _clean_path(self, path):
        path = path.replace("file:///", "").replace("file://", "")
        path = path.replace("%20", " ")
        return os.path.abspath(path)

    # --- COMMAND PROCESSOR ---
    def process_command(self, text):
        cmd = text.strip().lower()
        parts = cmd.split(" ")
        action = parts[0]

        # 1. HELP / OPTIONS
        if action in ["!help", "!options", "!commands"]:
            self.show_options.emit()

        # 2. ADD COMMAND (Hybrid Logic)
        elif action == "!add":
            if len(parts) < 2:
                self.status_message.emit("Usage: !add [name]...")
                return

            # Scenario A: In Playlist -> Add [song] to current
            if self.is_queue_mode and self.current_playlist_name and not self.current_playlist_name.startswith("_"):
                query = " ".join(parts[1:])
                found = self._find_song_by_query(query)
                if found:
                    self._add_path_to_playlist(self.current_playlist_name, found)
                else:
                    self.status_message.emit("Song not found")

            # Scenario B: Not in Playlist -> Add [playlist] [song]
            else:
                target_pl = parts[1]
                # B1: Add CURRENT song
                if len(parts) == 2:
                    if self.current_path:
                        self._add_path_to_playlist(target_pl, self.current_path)
                    else:
                        self.status_message.emit("No song playing")
                # B2: Add SEARCHED song
                else:
                    query = " ".join(parts[2:])
                    found = self._find_song_by_query(query)
                    if found:
                        self._add_path_to_playlist(target_pl, found)
                    else:
                        self.status_message.emit("Song not found")

        # 3. SHUFFLE
        elif action == "!shuffle":
            self.is_queue_mode = False
            self.queue = []
            self.current_playlist_name = None
            self.global_queue = [] 
            self.ensure_global_queue()
            self.status_message.emit("Library Reshuffled")
            self.skip_next()

        # 4. ARTIST LOOP
        elif action == "!artist" and len(parts) > 1:
            raw_query = " ".join(parts[1:])
            query_compressed = re.sub(r'\W+', '', raw_query).lower()
            valid_exts = {'.mp3', '.wav', '.flac', '.m4a', '.opus', '.webm', '.ogg'}
            matches = []
            for f in MUSIC_DIR.iterdir():
                if f.is_file() and f.suffix.lower() in valid_exts:
                    fname = f.stem.lower().replace("_", " ")
                    if query_compressed in re.sub(r'\W+', '', fname):
                        matches.append(str(f.absolute()))

            if matches:
                temp_name = f"_artist_{query_compressed}"
                self.playlists[temp_name] = matches
                self.current_playlist_name = temp_name
                self.queue = list(matches)
                random.shuffle(self.queue)
                self.is_queue_mode = True
                self.status_message.emit(f"Looping {raw_query.title()}")
                self.skip_next()
            else:
                self.status_message.emit(f"No songs for '{raw_query}'")

        # 5. REMOVE
        elif action == "!remove":
            if self.is_queue_mode and self.current_playlist_name:
                name = self.current_playlist_name
                if name.startswith("_"):
                    self.status_message.emit("Cannot remove from artist loop")
                elif self.current_path in self.playlists[name]:
                    self.playlists[name].remove(self.current_path)
                    self.save_playlists()
                    self.status_message.emit(f"Removed from {name}")
                    self.skip_next()
                else:
                    self.status_message.emit("Song not in playlist")
            else:
                self.status_message.emit("Not playing a playlist")

        # 6. CREATE
        elif action == "!create" and len(parts) > 1:
            name = parts[1]
            if name not in self.playlists:
                self.playlists[name] = []
                self.save_playlists()
                self.status_message.emit(f"Created: {name}")
            else:
                self.status_message.emit(f"Playlist {name} exists")

        # 7. PLAY PLAYLIST
        elif action == "!play" and len(parts) > 1:
            name = parts[1]
            if name in self.playlists and self.playlists[name]:
                self.current_playlist_name = name
                self.queue = list(self.playlists[name]) 
                random.shuffle(self.queue)
                self.is_queue_mode = True
                self.status_message.emit(f"Playing {name}")
                self.skip_next()
            else:
                self.status_message.emit(f"Playlist {name} empty")

        # 8. DELETE FILE
        elif action == "!delete":
            if self.current_path and os.path.exists(self.current_path):
                try:
                    target = self.current_path
                    self.player.stop() 
                    os.remove(target)
                    if target in self.global_queue: self.global_queue.remove(target)
                    if target in self.queue: self.queue.remove(target)
                    
                    # Clean from all playlists
                    cleaned = False
                    for pname, tracks in self.playlists.items():
                        if target in tracks:
                            tracks.remove(target)
                            cleaned = True
                    if cleaned: self.save_playlists()
                    
                    self.status_message.emit("Deleted & Skipped")
                    self.skip_next()
                except Exception as e:
                    self.status_message.emit("Error deleting file")
            else:
                self.status_message.emit("No file to delete")

        # 9. CONTROLS
        elif action == "!vol" and len(parts) > 1:
            try:
                vol = max(0, min(100, int(parts[1])))
                self.set_volume(vol, emit_signal=True)
                self.status_message.emit(f"Volume: {vol}%")
            except:
                self.status_message.emit("Invalid number")

        elif action == "!skip":
            self.skip_next()
            self.status_message.emit("Skipped")

        elif action == "!back":
            self.skip_back()
            self.status_message.emit("Previous Track")

        elif action in ["!exit", "!close", "!off"]:
            self.status_message.emit("Closing...")
            self.player.stop()
            sys.exit(0)

    # --- Helpers ---
    def toggle(self):
        if self.player.is_playing(): self.player.pause()
        else: self.player.play()

    def set_volume(self, val, emit_signal=False):
        self.current_volume = val
        self.player.audio_set_volume(val)
        with open(SETTINGS_FILE, "w") as f: json.dump({"volume": val}, f)
        if emit_signal: self.volume_changed.emit(val)

    def check_playback_status(self):
        if self.player.get_state() == vlc.State.Ended:
            self.skip_next()

    def get_volume(self): return self.current_volume
    def get_time(self): return max(0, self.player.get_time() / 1000)
    def get_position(self): return self.player.get_position()
    def set_position(self, pos): self.player.set_position(pos)
    def get_duration(self): return max(0, self.player.get_length() / 1000)


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Update Check (Prints to console)
    updater.check_for_updates()

    # 2. Start Application
    app = QApplication(sys.argv)
    
    # 3. Initialize Logic
    player = MusicPlayer()
    
    # 4. Initialize UI Windows
    search_win = SearchWindow(player)
    player_win = PlayerWindow(player)
    options_win = OptionsWindow(player)
    
    # 5. Connect Windows
    player.show_options.connect(options_win.show_animated)

    # 6. Show Initial UI
    search_win.show_search() # Search bar pops up
    player_win.toggle()      # Player bar pops up

    # 7. Run Event Loop
    sys.exit(app.exec())
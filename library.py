from pathlib import Path
import sys

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.absolute()
    else:
        return Path(__file__).parent.absolute()

BASE_DIR = get_app_dir()
MUSIC_DIR = BASE_DIR / "music"

def find_song(query):
    """Searches the local music folder for a matching file."""
    if not MUSIC_DIR.exists():
        return None
        
    query = query.lower()
    for file in MUSIC_DIR.iterdir():
        if file.is_file() and query in file.stem.lower():
            return file
    return None
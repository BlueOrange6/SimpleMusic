import yt_dlp
from pathlib import Path
import os
from helpers import get_app_dir

BASE_DIR = get_app_dir()
MUSIC_DIR = BASE_DIR / "music"
MUSIC_DIR.mkdir(exist_ok=True)

def _get_info(ydl, query):
    try:
        if "youtube.com" in query or "youtu.be" in query:
            return ydl.extract_info(query, download=True)
        else:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if 'entries' in info and len(info['entries']) > 0:
                return info['entries'][0]
            return None
    except Exception as e:
        print(f"Extraction Error: {e}")
        return None

def download_song(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(MUSIC_DIR / "%(title)s.%(ext)s"),
        "restrictfilenames": True,
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        video_data = _get_info(ydl, query)
        if not video_data: return None, None
        
        target_filename = ydl.prepare_filename(video_data)
        final_path = None
        
        if os.path.exists(target_filename): final_path = target_filename
        else:
            stem = Path(target_filename).stem
            for file in MUSIC_DIR.glob(f"{stem}*"):
                final_path = str(file)
                break
                
        if final_path:
            return os.path.abspath(final_path), video_data.get('title', query)
        return None, None
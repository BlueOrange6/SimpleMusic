import sys
import os
from pathlib import Path

def resource_path(relative_path):
    """Finds assets packed inside the PyInstaller .exe"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return str(Path(base_path) / relative_path)

def get_app_dir():
    """Finds the real folder where the .exe is sitting (Fixes Startup crash)"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.absolute()
    else:
        return Path(__file__).parent.absolute()
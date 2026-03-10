import os
import sys
import requests
import subprocess
from packaging import version

# --- CONFIG ---
CURRENT_VERSION = "1.0"
VERSION_URL = f"https://raw.githubusercontent.com/BlueOrange6/SimpleMusic/refs/heads/main/version.txt"
EXE_URL = f"https://github.com/BlueOrange6/SimpleMusic/releases/latest/download/SimpleMusic.exe"

def check_for_updates():
    if os.path.exists("SimpleMusic.old"):
        try: os.remove("SimpleMusic.old")
        except: pass

    try:
        print(f"Checking updates... (Current: {CURRENT_VERSION})")
        # Timeout is fast so we don't block startup if offline
        resp = requests.get(VERSION_URL, timeout=2) 
        
        if version.parse(resp.text.strip()) > version.parse(CURRENT_VERSION):
            print(f"Update found: {resp.text.strip()}. Downloading...")
            _perform_update()
            return True
            
    except Exception as e:
        print(f"Skipping update check: {e}")
    
    return False

def _perform_update():
    if getattr(sys, 'frozen', False):
        current_exe = sys.executable
        renamed_exe = current_exe.replace(".exe", ".old")
        
        try:
            os.rename(current_exe, renamed_exe)
            
            # STREAM DOWNLOAD (Prevents memory spikes)
            with requests.get(EXE_URL, stream=True) as r:
                r.raise_for_status()
                total_length = r.headers.get('content-length')
                
                with open(current_exe, 'wb') as f:
                    if total_length is None: # No content length header
                        f.write(r.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        # Download in chunks
                        for chunk in r.iter_content(chunk_size=8192):
                            dl += len(chunk)
                            f.write(chunk)
                            
                            # Calculate percentage
                            done = int(50 * dl / total_length)
                            # Print progress bar to console [===  ]
                            sys.stdout.write(f"\rDownloading Update: [{'=' * done}{' ' * (50-done)}] {int(dl/total_length*100)}%")
                            sys.stdout.flush()

            print("\nDownload complete. Restarting...")
            subprocess.Popen([current_exe])
            sys.exit()

        except Exception as e:
            print(f"\nUpdate Failed: {e}")
            if os.path.exists(renamed_exe):
                if os.path.exists(current_exe): os.remove(current_exe)
                os.rename(renamed_exe, current_exe)
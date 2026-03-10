# 🎵 SimpleMusic

A lightweight, command-driven, frameless music player for Windows that lives in your system tray. Built with Python and PyQt6, SimpleMusic combines a sleek, minimal interface with powerful features like instant YouTube downloading, global hotkeys, and an auto-updater.

## ✨ Features
* **Command-Driven UI:** Control everything from a single search bar using `!commands`.
* **Integrated YouTube Downloader:** Type a song name to instantly download and play it via `yt-dlp`.
* **System Tray Integration:** Runs quietly in the background. 
* **Global Hotkeys:** Control playback or bring up the search bar from anywhere on your PC.
* **Auto-Updating:** Automatically detects and installs new releases from GitHub.
* **Run on Startup:** Easily toggle Windows startup directly from the options menu.

---

## 🚀 Installation (For Normal Users)

1. Go to the [Releases](../../releases/latest) tab on the right side of this page.
2. Download **`SimpleMusic.exe`**.
3. Place the `.exe` in a dedicated folder (e.g., `C:\SimpleMusic\`). It will generate its `music/` and `settings.json` files right next to it.
4. Double-click to run! 

> **⚠️ Windows Security Note:** Because this is a free, unsigned application, Windows SmartScreen or Smart App Control might show a blue warning. Click **"More info"** and **"Run anyway"**. If it gets blocked entirely, right-click the file -> Properties -> check **"Unblock"** -> Apply.

*Note: SimpleMusic requires VLC Media Player to be installed on your system to process audio.*

---

## ⌨️ Controls & Commands

To open the command bar, press **`Ctrl + Alt + S`** (or click the System Tray icon).

### Global Shortcuts
* `Ctrl + Alt + S` : Open Search / Command Bar
* `Ctrl + Alt + P` : Toggle Player Bar visibility
* `Media Play/Pause` : Play / Pause track
* `Media Next/Prev` : Skip or go back

### App Commands
Type these directly into the search bar:
* `!play <playlist>` - Start a specific playlist
* `!shuffle` - Shuffle all downloaded songs
* `!artist <name>` - Loop all songs containing that artist's name
* `!add <playlist>` - Add the *currently playing* song to a playlist
* `!add <playlist> <song>` - Search, download, and add a specific song to a playlist
* `!create <name>` - Create a new empty playlist
* `!remove` - Remove the current song from the active playlist
* `!delete` - Permanently delete the current song file from your PC
* `!vol <0-100>` - Set the volume
* `!help` or `!options` - Open the settings menu
* `!exit` - Completely close the application

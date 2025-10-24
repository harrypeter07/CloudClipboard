import os
from pathlib import Path

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")  # Local server URL

# Local storage
CONFIG_DIR = Path.home() / ".cloudclipboard"
CONFIG_FILE = CONFIG_DIR / "config.json"

CONFIG_DIR.mkdir(exist_ok=True)

# Hotkeys
HOTKEY_HISTORY = 'ctrl+shift+v'
HOTKEY_GHOST_MODE = 'ctrl+7'
HOTKEY_GHOST_PASTE = 'ctrl+shift+7'  # For secret paste

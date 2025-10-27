import os
from pathlib import Path

# API Configuration
API_URL = os.getenv("API_URL", "https://cloudclipboard.onrender.com")  # Render deployment URL

# Local storage
CONFIG_DIR = Path.home() / ".cloudclipboard"
CONFIG_FILE = CONFIG_DIR / "config.json"

CONFIG_DIR.mkdir(exist_ok=True)

# Hotkeys
HOTKEY_HISTORY = 'ctrl+shift+h'  # Changed to avoid conflict
HOTKEY_GHOST_MODE = 'ctrl+7'
HOTKEY_GHOST_PASTE = 'ctrl+shift+v'  # Auto-paste last item

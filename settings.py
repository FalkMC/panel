import os
import sys
import json

# Dir where its located, settings.json lives here
def get_app_dir():
    if getattr(sys, 'frozen', False):
        # Running as .exe – settings go next to the .exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script – settings go next to main.py
        return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")
VERSION = 1

DEFAULT_SETTINGS = {
    "version": VERSION,
    "theme": "dark",
    "window_width": 1152,
    "window_height": 648
}

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    with open(SETTINGS_PATH, "r") as f:
        data = json.load(f)
    if data.get("version") != VERSION:
        merged = DEFAULT_SETTINGS.copy()
        for key, value in data.items():
            if key in merged:
                merged[key] = value
        merged["version"] = VERSION
        save_settings(merged)
        return merged
    return data

def save_settings(data):
    data["version"] = VERSION
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)

import os
import json

DOCUMENTS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
FALKMC_DIR = os.path.join(DOCUMENTS_DIR, "FalkMC")
os.makedirs(FALKMC_DIR, exist_ok=True)

SETTINGS_PATH = os.path.join(FALKMC_DIR, "settings.json")
VERSION = 1

DEFAULT_SETTINGS = {
    "version": VERSION,
    "theme": "dark",
    "window_width": 1000,
    "window_height": 545
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

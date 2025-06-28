import json
from pathlib import Path
import os

DEFAULT_SETTINGS = {
    "highlight_size": 40,
    "highlight_color": (255, 0, 0, 128),
    "export_path": os.path.expanduser("~/Documents"),
}

CONFIG_PATH = Path("configs.json")


def load_settings():
    """Load persisted settings and return a settings dict."""
    settings = DEFAULT_SETTINGS.copy()
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as fh:
                data = json.load(fh)
            for key in DEFAULT_SETTINGS:
                if key in data:
                    val = data[key]
                    if isinstance(DEFAULT_SETTINGS[key], tuple) and isinstance(val, list):
                        val = tuple(val)
                    settings[key] = val
        except Exception as e:
            print(f"Failed to load settings: {e}")
    return settings


def save_settings(settings):
    """Persist the given settings to CONFIG_PATH."""
    try:
        data = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as fh:
                data = json.load(fh)
        for key in DEFAULT_SETTINGS:
            val = settings.get(key, DEFAULT_SETTINGS[key])
            if isinstance(val, tuple):
                val = list(val)
            data[key] = val
        with open(CONFIG_PATH, "w") as fh:
            json.dump(data, fh, indent=2)
    except Exception as e:
        print(f"Failed to save settings: {e}")


current_settings = load_settings()

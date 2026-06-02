from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
DEFAULT_OUTPUT = Path.home() / "Downloads" / "video-downloader"
IMPORTS_DIR = Path.home() / "Movies" / "Imports"


def _ensure_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    _ensure_data()
    if SETTINGS_FILE.is_file():
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    return default_settings()


def default_settings() -> dict:
    return {
        "output_dir": str(DEFAULT_OUTPUT),
        "move_to_imports": False,
        "imports_dir": str(IMPORTS_DIR),
    }


def save_settings(data: dict) -> dict:
    _ensure_data()
    current = default_settings()
    current.update({k: v for k, v in data.items() if k in current})
    out = Path(current["output_dir"]).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current


def get_output_dir() -> Path:
    s = load_settings()
    p = Path(s["output_dir"]).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_imports_dir() -> Path:
    s = load_settings()
    p = Path(s.get("imports_dir", str(IMPORTS_DIR))).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def should_move_to_imports() -> bool:
    return bool(load_settings().get("move_to_imports"))

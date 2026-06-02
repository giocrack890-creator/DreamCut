from __future__ import annotations

from typing import Any

PROFILES: dict[str, dict[str, Any]] = {
    "mobile_720": {
        "name": "Móvil 720p",
        "kind": "mp4",
        "format_id": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "description": "MP4 hasta 720p",
    },
    "archive_1080": {
        "name": "Archivo 1080p",
        "kind": "mp4",
        "format_id": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "description": "MP4 hasta 1080p",
    },
    "podcast_mp3": {
        "name": "Podcast MP3",
        "kind": "mp3",
        "format_id": "bestaudio/best",
        "quick_mp3": True,
        "description": "MP3 192 kbps",
    },
}


def list_profiles() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in PROFILES.items()]


def get_profile(profile_id: str) -> dict[str, Any] | None:
    p = PROFILES.get(profile_id)
    if not p:
        return None
    return {"id": profile_id, **p}

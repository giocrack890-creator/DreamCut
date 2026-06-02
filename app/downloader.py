from __future__ import annotations

import app.ssl_certs  # noqa: F401

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from app.config import get_imports_dir, get_output_dir, should_move_to_imports
from app.history import add_entry

SUPPORTED_HOSTS = (
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "twitch.tv",
    "clips.twitch.tv",
)

URL_RE = re.compile(r"^https?://", re.I)
TIME_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{1,2})$|^(\d+(?:\.\d+)?)$")

CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

ProgressCallback = Callable[[float, str], None]


@dataclass
class DownloadRequest:
    url: str
    format_id: str = "best"
    kind: str = "mp4"
    output_dir: Path | None = None
    trim_start: str | None = None
    trim_end: str | None = None
    subtitle_langs: list[str] = field(default_factory=list)
    quick_mp3: bool = False
    move_to_imports: bool | None = None


def _sort_height(label: str) -> int:
    m = re.search(r"(\d+)p", label or "", re.I)
    return int(m.group(1)) if m else 0


def _sort_bitrate(label: str) -> int:
    m = re.search(r"(\d+)\s*kbps", label or "", re.I)
    return int(m.group(1)) if m else 0


def _host(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url, flags=re.I).split("/")[0].lower()


def _is_tiktok(url: str) -> bool:
    return "tiktok" in _host(url)


def _is_youtube(url: str) -> bool:
    h = _host(url)
    return h.endswith("youtube.com") or h == "youtu.be"


def is_channel_url(url: str) -> bool:
    if not _is_youtube(url):
        return False
    return any(
        x in url
        for x in ("/@", "/channel/", "/user/", "/c/", "/videos")
    ) and "watch?v=" not in url


def _ydl_opts(url: str = "", **extra: Any) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": extra.pop("noplaylist", True),
        "socket_timeout": 60,
        "retries": 5,
        "fragment_retries": 5,
        "http_headers": {
            "User-Agent": CHROME_UA,
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        },
    }
    if _is_tiktok(url):
        opts["http_headers"]["Referer"] = "https://www.tiktok.com/"
    opts.update(extra)
    return opts


def normalize_url(url: str) -> str:
    url = url.strip()
    if not URL_RE.match(url):
        raise ValueError("El enlace debe empezar con http:// o https://")
    host = _host(url)
    if not any(host == h or host.endswith("." + h) for h in SUPPORTED_HOSTS):
        raise ValueError(
            "Plataforma no soportada. Usa YouTube, TikTok, Instagram, X o Twitch."
        )
    return url


def parse_time(value: str | None) -> float | None:
    if not value or not str(value).strip():
        return None
    s = str(value).strip()
    m = TIME_RE.match(s)
    if not m:
        raise ValueError(f"Tiempo inválido: {value} (usa 1:30 o segundos)")
    if m.group(4):
        return float(m.group(4))
    h, mi, se = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
    return h * 3600 + mi * 60 + se


def _human_size(n: int | float | None) -> str:
    if not n:
        return "—"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TB"


def _video_label(fmt: dict[str, Any]) -> str:
    parts: list[str] = []
    h = fmt.get("height")
    if h:
        parts.append(f"{h}p")
    ext = (fmt.get("ext") or "mp4").upper()
    parts.append(ext)
    note = fmt.get("format_note") or fmt.get("quality")
    if note:
        parts.append(str(note))
    return " · ".join(parts) if parts else fmt.get("format_id", "video")


def _audio_label(fmt: dict[str, Any]) -> str:
    parts: list[str] = []
    abr = fmt.get("abr") or fmt.get("tbr")
    if abr:
        parts.append(f"{int(abr)} kbps")
    ext = (fmt.get("ext") or "m4a").upper()
    parts.append(ext)
    return " · ".join(parts) if parts else fmt.get("format_id", "audio")


def _progress_hook(cb: ProgressCallback | None) -> Callable[[dict], None]:
    def hook(d: dict) -> None:
        if not cb:
            return
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            if total:
                cb(min(99.0, done * 100.0 / total), "Descargando…")
            else:
                cb(50.0, "Descargando…")
        elif d.get("status") == "finished":
            cb(95.0, "Procesando…")

    return hook


def list_channel_videos(url: str, limit: int = 20) -> dict[str, Any]:
    url = normalize_url(url)
    if not _is_youtube(url):
        raise ValueError("El modo canal solo está disponible para YouTube")
    limit = max(1, min(limit, 50))
    opts = _ydl_opts(
        url,
        extract_flat="in_playlist",
        skip_download=True,
        playlistend=limit,
        noplaylist=False,
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = []
    for e in info.get("entries") or []:
        if not e:
            continue
        vid_url = e.get("url") or e.get("webpage_url")
        if not vid_url and e.get("id"):
            vid_url = f"https://www.youtube.com/watch?v={e['id']}"
        if vid_url:
            entries.append(
                {
                    "id": e.get("id"),
                    "title": e.get("title") or "Sin título",
                    "url": vid_url,
                    "duration": e.get("duration"),
                    "thumbnail": e.get("thumbnail"),
                }
            )
    return {
        "channel": info.get("title") or info.get("uploader") or "Canal",
        "videos": entries[:limit],
    }


def analyze(url: str) -> dict[str, Any]:
    url = normalize_url(url)
    opts = _ydl_opts(url, skip_download=True)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise ValueError("Lista vacía")
        info = entries[0]

    formats = info.get("formats") or []
    tiktok = _is_tiktok(url)
    mp4_options: list[dict[str, Any]] = []
    seen_video: set[str] = set()

    for fmt in formats:
        if fmt.get("vcodec") in (None, "none"):
            continue
        fid = fmt.get("format_id")
        if not fid or fid in seen_video:
            continue
        ext = (fmt.get("ext") or "").lower()
        if not tiktok and ext not in ("mp4", "webm", "mkv", "mov"):
            continue
        key = f"{fmt.get('height')}-{ext}"
        if key in seen_video:
            continue
        seen_video.add(key)
        seen_video.add(fid)
        mp4_options.append(
            {
                "format_id": fid,
                "label": _video_label(fmt),
                "size": _human_size(fmt.get("filesize") or fmt.get("filesize_approx")),
            }
        )

    mp4_options.sort(key=lambda x: _sort_height(x["label"]), reverse=True)

    mp3_options: list[dict[str, Any]] = []
    seen_audio: set[str] = set()
    for fmt in formats:
        if fmt.get("acodec") in (None, "none") or fmt.get("vcodec") not in (None, "none"):
            continue
        fid = fmt.get("format_id")
        if not fid or fid in seen_audio:
            continue
        abr = fmt.get("abr") or fmt.get("tbr") or 0
        try:
            key = str(int(float(abr)))
        except (TypeError, ValueError):
            key = str(fid)
        if key in seen_audio:
            continue
        seen_audio.add(key)
        mp3_options.append(
            {
                "format_id": fid,
                "label": _audio_label(fmt),
                "size": _human_size(fmt.get("filesize") or fmt.get("filesize_approx")),
            }
        )
    mp3_options.sort(key=lambda x: _sort_bitrate(x["label"]), reverse=True)

    if not mp4_options:
        mp4_options.append(
            {"format_id": "bestvideo+bestaudio/best", "label": "Mejor calidad", "size": "—"}
        )
    if not mp3_options:
        mp3_options.append({"format_id": "bestaudio/best", "label": "Mejor audio", "size": "—"})

    thumb = info.get("thumbnail")
    thumbnails = info.get("thumbnails") or []
    if not thumb and thumbnails:
        thumb = thumbnails[-1].get("url")

    return {
        "title": info.get("title") or "Sin título",
        "thumbnail": thumb,
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel"),
        "webpage_url": info.get("webpage_url") or url,
        "mp4": mp4_options[:12],
        "mp3": mp3_options[:8],
        "is_channel": is_channel_url(url),
    }


def _ffmpeg_trim(src: Path, start: float | None, end: float | None) -> Path:
    if start is None and end is None:
        return src
    out = src.with_name(src.stem + "_trim" + src.suffix)
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if start is not None:
        cmd.extend(["-ss", str(start)])
    if end is not None:
        cmd.extend(["-to", str(end)])
    cmd.extend(["-c", "copy", str(out)])
    subprocess.run(cmd, check=True, capture_output=True)
    src.unlink(missing_ok=True)
    return out


def _finalize_path(path: Path, move_imports: bool) -> Path:
    if move_imports:
        dest_dir = get_imports_dir()
        dest = dest_dir / path.name
        shutil.move(str(path), str(dest))
        return dest
    return path


def download(req: DownloadRequest, on_progress: ProgressCallback | None = None) -> Path:
    url = normalize_url(req.url)
    out_dir = req.output_dir or get_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="vdl_"))
    outtmpl = str(work / "%(title).200B.%(ext)s")

    kind = req.kind
    format_id = req.format_id
    if req.quick_mp3 or (kind == "mp3" and format_id in ("quick", "bestaudio/best", "best")):
        kind = "mp3"
        format_id = "bestaudio/best"

    ydl_opts = _ydl_opts(
        url,
        format=format_id,
        outtmpl=outtmpl,
        progress_hooks=[_progress_hook(on_progress)],
    )

    if kind == "mp3":
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        ydl_opts["merge_output_format"] = "mp4"

    if req.subtitle_langs:
        ydl_opts["writesubtitles"] = True
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = req.subtitle_langs
        ydl_opts["subtitlesformat"] = "srt"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info.get("_type") == "playlist":
            entries = [e for e in (info.get("entries") or []) if e]
            info = entries[0] if entries else info

    media = sorted(
        [p for p in work.iterdir() if p.is_file() and p.suffix.lower() in (".mp4", ".mp3", ".m4a", ".webm", ".mkv")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not media:
        raise RuntimeError("No se generó ningún archivo")

    path = media[0]
    if kind == "mp3" and path.suffix.lower() != ".mp3":
        mp3s = list(work.glob("*.mp3"))
        if mp3s:
            path = mp3s[0]

    start = parse_time(req.trim_start)
    end = parse_time(req.trim_end)
    if start is not None or end is not None:
        if on_progress:
            on_progress(96.0, "Recortando…")
        path = _ffmpeg_trim(path, start, end)

    title = (info.get("title") or "download")[:180]
    safe = re.sub(r'[<>:"/\\|?*]', "", title).strip() or "download"
    ext = ".mp3" if kind == "mp3" else path.suffix or ".mp4"
    final = out_dir / f"{safe}{ext}"
    if final.exists():
        final = out_dir / f"{safe}_{path.stat().st_mtime_ns}{ext}"
    shutil.move(str(path), str(final))

    for sub in work.glob("*.srt"):
        dest_sub = out_dir / sub.name
        shutil.move(str(sub), str(dest_sub))

    shutil.rmtree(work, ignore_errors=True)

    move = req.move_to_imports if req.move_to_imports is not None else should_move_to_imports()
    final = _finalize_path(final, move)

    if on_progress:
        on_progress(100.0, "Listo")

    add_entry(url, title, kind, str(final))
    return final


def download_to_temp(
    url: str,
    format_id: str,
    kind: str,
    trim_start: str | None = None,
    trim_end: str | None = None,
    subtitle_langs: list[str] | None = None,
    quick_mp3: bool = False,
    move_to_imports: bool = False,
) -> tuple[Path, str]:
    tmp = Path(tempfile.mkdtemp(prefix="vdl_"))
    req = DownloadRequest(
        url=url,
        format_id=format_id,
        kind=kind,
        output_dir=tmp,
        trim_start=trim_start,
        trim_end=trim_end,
        subtitle_langs=subtitle_langs or [],
        quick_mp3=quick_mp3,
        move_to_imports=move_to_imports,
    )
    path = download(req)
    return path, path.name

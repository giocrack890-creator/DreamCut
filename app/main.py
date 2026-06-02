from __future__ import annotations

import app.ssl_certs  # noqa: F401

import asyncio
import re
import shutil
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import default_settings, load_settings, save_settings
from app.downloader import (
    DownloadRequest,
    analyze,
    download_to_temp,
    is_channel_url,
    list_channel_videos,
    normalize_url,
)
from app.history import init_db, list_entries
from app.profiles import get_profile, list_profiles
from app.queue_manager import queue_manager

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

app = FastAPI(title="Video Downloader", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


class AnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=8)


class ChannelRequest(BaseModel):
    url: str
    limit: int = Field(20, ge=1, le=50)


class SettingsUpdate(BaseModel):
    output_dir: str | None = None
    move_to_imports: bool | None = None
    imports_dir: str | None = None


class QueueItem(BaseModel):
    url: str
    format_id: str = "best"
    kind: str = "mp4"
    trim_start: str | None = None
    trim_end: str | None = None
    subtitle_langs: list[str] = Field(default_factory=list)
    quick_mp3: bool = False
    profile_id: str | None = None


class QueueBatch(BaseModel):
    items: list[QueueItem]


def _clean_error(msg: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", msg).strip()


def _item_to_request(item: QueueItem) -> DownloadRequest:
    if item.profile_id:
        p = get_profile(item.profile_id)
        if not p:
            raise ValueError(f"Perfil desconocido: {item.profile_id}")
        return DownloadRequest(
            url=item.url,
            format_id=p["format_id"],
            kind=p["kind"],
            trim_start=item.trim_start,
            trim_end=item.trim_end,
            subtitle_langs=item.subtitle_langs,
            quick_mp3=bool(p.get("quick_mp3")),
        )
    return DownloadRequest(
        url=item.url,
        format_id=item.format_id,
        kind=item.kind,
        trim_start=item.trim_start,
        trim_end=item.trim_end,
        subtitle_langs=item.subtitle_langs,
        quick_mp3=item.quick_mp3,
    )


@app.get("/api/health")
def api_health():
    return {"ok": True}


@app.get("/api/settings")
def api_get_settings():
    return load_settings()


@app.put("/api/settings")
def api_put_settings(body: SettingsUpdate):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return save_settings(data)


@app.get("/api/profiles")
def api_profiles():
    return list_profiles()


@app.get("/api/history")
def api_history(limit: int = Query(50, ge=1, le=200)):
    return list_entries(limit)


@app.post("/api/analyze")
async def api_analyze(body: AnalyzeRequest):
    try:
        return await asyncio.to_thread(analyze, body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=_clean_error(str(e))) from e


@app.post("/api/channel")
async def api_channel(body: ChannelRequest):
    try:
        return await asyncio.to_thread(list_channel_videos, body.url, body.limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=_clean_error(str(e))) from e


@app.get("/api/channel/detect")
def api_channel_detect(url: str = Query(...)):
    try:
        normalize_url(url)
        return {"is_channel": is_channel_url(url)}
    except ValueError:
        return {"is_channel": False}


@app.post("/api/queue")
async def api_queue_add(body: QueueBatch):
    try:
        ids = []
        for item in body.items:
            req = _item_to_request(item)
            ids.append(queue_manager.add(req))
        return {"job_ids": ids, "jobs": queue_manager.list_jobs()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/queue")
def api_queue_list():
    return queue_manager.list_jobs()


@app.get("/api/download")
async def api_download(
    url: str = Query(...),
    format_id: str = Query(...),
    kind: str = Query(..., pattern="^(mp3|mp4)$"),
    trim_start: str | None = None,
    trim_end: str | None = None,
    subs_es: bool = False,
    subs_en: bool = False,
    quick_mp3: bool = False,
    profile_id: str | None = None,
    move_to_imports: bool = False,
):
    try:
        langs: list[str] = []
        if subs_es:
            langs.append("es")
        if subs_en:
            langs.append("en")
        fid, k = format_id, kind
        qm = quick_mp3
        if profile_id:
            p = get_profile(profile_id)
            if not p:
                raise ValueError("Perfil desconocido")
            fid, k = p["format_id"], p["kind"]
            qm = bool(p.get("quick_mp3"))
        normalize_url(url)
        path, filename = await asyncio.to_thread(
            download_to_temp,
            url,
            fid,
            k,
            trim_start,
            trim_end,
            langs,
            qm,
            move_to_imports,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=_clean_error(str(e))) from e

    media = "audio/mpeg" if kind == "mp3" or quick_mp3 else "video/mp4"

    def cleanup():
        shutil.rmtree(path.parent, ignore_errors=True)

    return FileResponse(path, media_type=media, filename=filename, background=cleanup)


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")

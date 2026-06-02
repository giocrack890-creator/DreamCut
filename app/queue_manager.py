from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_output_dir
from app.downloader import DownloadRequest, download


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class QueueJob:
    id: str
    request: DownloadRequest
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    message: str = ""
    error: str | None = None
    output_path: str | None = None
    title: str | None = None


class QueueManager:
    def __init__(self) -> None:
        self._jobs: dict[str, QueueJob] = {}
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def add(self, req: DownloadRequest) -> str:
        jid = str(uuid.uuid4())[:8]
        job = QueueJob(id=jid, request=req)
        with self._lock:
            self._jobs[jid] = job
        return jid

    def add_many(self, requests: list[DownloadRequest]) -> list[str]:
        return [self.add(r) for r in requests]

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        out = []
        for j in sorted(jobs, key=lambda x: x.id):
            out.append(
                {
                    "id": j.id,
                    "url": j.request.url,
                    "kind": j.request.kind,
                    "status": j.status.value,
                    "progress": j.progress,
                    "message": j.message,
                    "error": j.error,
                    "output_path": j.output_path,
                }
            )
        return out

    def _update(self, jid: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(jid)
            if job:
                for k, v in kwargs.items():
                    setattr(job, k, v)

    def _run(self) -> None:
        while True:
            jid = None
            with self._lock:
                for job in self._jobs.values():
                    if job.status == JobStatus.PENDING:
                        jid = job.id
                        job.status = JobStatus.RUNNING
                        break
            if not jid:
                threading.Event().wait(0.5)
                continue

            with self._lock:
                job = self._jobs[jid]

            def prog(p: float, msg: str) -> None:
                self._update(jid, progress=p, message=msg)

            try:
                if not job.request.output_dir:
                    job.request.output_dir = get_output_dir()
                path = download(job.request, on_progress=prog)
                self._update(
                    jid,
                    status=JobStatus.DONE,
                    progress=100.0,
                    message="Completado",
                    output_path=str(path),
                )
            except Exception as e:
                self._update(
                    jid,
                    status=JobStatus.ERROR,
                    error=str(e),
                    message="Error",
                )


queue_manager = QueueManager()

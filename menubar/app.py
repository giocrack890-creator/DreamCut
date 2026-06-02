#!/usr/bin/env python3
"""App de barra de menú macOS para el descargador."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import webbrowser
from pathlib import Path

import rumps

ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
URL = "http://127.0.0.1:8765"
PORT = 8765


class VideoDownloaderMenubar(rumps.App):
    def __init__(self) -> None:
        super().__init__("⬇️ Video DL", quit_button=None)
        self.server_proc: subprocess.Popen | None = None
        self.menu = [
            rumps.MenuItem("Iniciar servidor", callback=self.toggle_server),
            rumps.MenuItem("Abrir en navegador", callback=self.open_web),
            rumps.MenuItem("Abrir carpeta de descargas", callback=self.open_downloads),
            None,
            rumps.MenuItem("Salir", callback=rumps.quit_application),
        ]

    def _server_running(self) -> bool:
        try:
            import urllib.request

            urllib.request.urlopen(f"{URL}/api/health", timeout=1)
            return True
        except Exception:
            return False

    @rumps.clicked("Iniciar servidor")
    def toggle_server(self, _: object) -> None:
        if self._server_running():
            if self.server_proc:
                self.server_proc.terminate()
                self.server_proc = None
            rumps.notification("Video DL", "", "Servidor detenido (si lo iniciaste desde aquí)")
            return
        py = VENV_PYTHON if VENV_PYTHON.is_file() else Path(sys.executable)
        self.server_proc = subprocess.Popen(
            [str(py), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
        )
        rumps.notification("Video DL", "", "Servidor iniciado en " + URL)

    @rumps.clicked("Abrir en navegador")
    def open_web(self, _: object) -> None:
        if not self._server_running():
            rumps.alert("Servidor apagado", "Pulsa «Iniciar servidor» primero.")
            return
        webbrowser.open(URL)

    @rumps.clicked("Abrir carpeta de descargas")
    def open_downloads(self, _: object) -> None:
        path = Path.home() / "Downloads" / "video-downloader"
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(path)], check=False)


if __name__ == "__main__":
    VideoDownloaderMenubar().run()

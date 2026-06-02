Lancé DreamCut: descargador de video 100% local.  YouTube · TikTok · IG · X · Twitch → MP4/MP3 con calidades → Cola + canal + perfiles → Extensión Chrome + menú macOS  Sin webs raras. Todo en tu Mac.

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/1c2664e2-b186-49df-8a1a-6bed898e97d2" />


### Pega un enlace. Elige calidad. Descarga.

**DreamCut** es un descargador de video **100% local**: sin cuentas raras, sin webs de terceros, sin subir tus enlaces a la nube. Analiza el video, te muestra formatos en **MP4** y **MP3**, y descarga en tu Mac con un clic.

Hecho para quien quiere control: cola de descargas, perfiles de calidad, recorte, subtítulos, historial y extensión de Chrome que habla solo con tu máquina.

---

## Por qué DreamCut

| Lo que odias | Lo que hace DreamCut |
|--------------|----------------------|
| Páginas llenas de anuncios y popups | Interfaz oscura tipo app pro, en tu navegador |
| “Descargadores” que no sabes dónde van tus datos | Servidor en `127.0.0.1` — todo en tu PC |
| Elegir calidad a ciegas | Lista clara: 1080p, 720p, MP3 192k… |
| Un video a la vez | **Cola** con barra de progreso |
| Canales enteros a mano | Modo **canal** YouTube (últimos N vídeos) |

---

## Plataformas soportadas

YouTube · TikTok · Instagram · X (Twitter) · Twitch

---

## Capturas

> Sustituye estas imágenes por capturas reales cuando publiques el repo (`docs/screenshot-web.png`, `docs/screenshot-extension.png`).

| Panel web | Extensión Chrome |
|-----------|------------------|
| Interfaz DreamCut con glass UI | Popup en la barra del navegador |

---

## Funciones principales

- **Análisis instantáneo** — título, miniatura, formatos MP4/MP3
- **MP3 rápido** — un botón, 192 kbps, sin menús
- **Perfiles** — Móvil 720p · Archivo 1080p · Podcast MP3
- **Cola de descargas** — pega 10 enlaces, mira el % en vivo
- **Modo canal** — URL de canal YouTube → elige qué vídeos bajar
- **Subtítulos** — `.srt` en español e inglés
- **Recorte** — `desde 0:30 hasta 1:45` con ffmpeg
- **Historial** — SQLite con título, fecha y ruta del archivo
- **Carpeta configurable** — o enviar todo a `~/Movies/Imports`
- **Extensión Chrome** — detecta el video de la pestaña activa
- **Menú macOS** — icono en la barra: servidor + abrir panel

---

## Inicio rápido

### Requisitos

- **Python 3.10+**
- **[ffmpeg](https://ffmpeg.org/)** (MP3 y algunos MP4)

```bash
brew install ffmpeg   # macOS
```

### Instalación

```bash
git clone https://github.com/giocrack890-creator/DreamCut.git
cd DreamCut
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

Abre **http://127.0.0.1:8765**

### Extensión Chrome

```bash
python3 chrome-extension/generate_icons.py   # solo la primera vez
```

1. Ejecuta `./run.sh` (el servidor debe estar activo).
2. Chrome → `chrome://extensions` → **Modo desarrollador** → **Cargar descomprimida**.
3. Carpeta: `chrome-extension/`.

### Barra de menú (macOS)

```bash
pip install -r menubar/requirements.txt
chmod +x menubar/run-menubar.sh
./menubar/run-menubar.sh
```

---

## Stack

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — extracción de video/audio
- **[FastAPI](https://fastapi.tiangolo.com/)** — API local
- **SQLite** — historial de descargas
- **ffmpeg** — MP3, merge y recorte

---

## Estructura del proyecto

```text
video-downloader/
├── app/                 # Backend (analyze, download, cola, historial)
├── static/              # Panel web DreamCut
├── chrome-extension/    # Extensión Chrome
├── menubar/             # App barra de menú macOS
├── data/                # settings + history.db (local, no se sube a git)
└── run.sh               # Arranque en un comando
```

---

## API local (resumen)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/health` | Estado del servidor |
| `POST` | `/api/analyze` | Analizar enlace |
| `GET` | `/api/download` | Descargar (query: url, format_id, kind) |
| `POST` | `/api/queue` | Encolar descargas |
| `GET` | `/api/queue` | Estado de la cola |
| `POST` | `/api/channel` | Listar vídeos de un canal |
| `GET` | `/api/history` | Historial |
| `GET` | `/api/profiles` | Perfiles predefinidos |

---

## macOS: error SSL

Si ves `CERTIFICATE_VERIFY_FAILED`:

```bash
open "/Applications/Python 3.14/Install Certificates.command"
```

(Ajusta la versión de Python si es distinta.)

---

## Uso responsable

DreamCut es una herramienta personal para contenido que **tienes derecho a guardar**. Respeta los términos de cada plataforma y las leyes de copyright de tu país. El autor no se hace responsable del uso indebido.

---

## Contribuir

Issues y PRs bienvenidos. Antes de abrir un PR, describe el caso (plataforma, enlace de ejemplo si es posible, error en terminal).

---

## Licencia

MIT — úsalo, modifícalo, mejóralo. Si te sirve, deja una estrella en el repo.

---

<p align="center">
  <strong>DreamCut</strong> — tus descargas, tu máquina, tu reglas.<br>
  Hecho con Python, café y cero trackers.
</p>

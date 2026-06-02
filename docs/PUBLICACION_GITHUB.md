# Texto listo para publicar en GitHub

Copia y pega según dónde lo publiques.

---

## Descripción corta (campo "About" del repositorio)

```
DreamCut — Descargador local de YouTube, TikTok, Instagram, X y Twitch. MP4/MP3, cola, perfiles, extensión Chrome. 100% en tu Mac, sin nube.
```

**Topics sugeridos:** `youtube-downloader` `tiktok` `yt-dlp` `fastapi` `chrome-extension` `python` `macos` `mp3` `video-downloader` `privacy`

---

## Título del repositorio (opcional)

```
dreamcut — video downloader local (YouTube, TikTok, MP4/MP3)
```

---

## Publicación tipo Release / Announcement

```markdown
## DreamCut está aquí

¿Cansado de páginas de descarga llenas de anuncios y enlaces sospechosos?

**DreamCut** es un descargador de video que corre **solo en tu computadora**:

- Pega un enlace de **YouTube, TikTok, Instagram, X o Twitch**
- Elige **MP4** (varias calidades) o **MP3** (incluye botón rápido 192k)
- **Cola** de descargas con progreso en tiempo real
- **Modo canal** para YouTube (últimos N vídeos)
- **Perfiles**: 720p móvil, 1080p archivo, podcast MP3
- Subtítulos `.srt`, recorte con ffmpeg, historial local
- **Extensión Chrome** + app de **barra de menú** en macOS

### Por qué es distinto

Todo pasa por `http://127.0.0.1:8765`. Tus enlaces no salen de tu máquina hacia servidores de terceros para “procesar” el video.

### Empieza en 30 segundos

```bash
git clone https://github.com/giocrack890-creator/DreamCut.git
cd video-downloader && ./run.sh
```

Abre http://127.0.0.1:8765 y listo.

⭐ Si te sirve, una estrella ayuda mucho.

_Uso personal y responsable. Respeta copyright y los ToS de cada plataforma._
```

---

## Tweet / post corto (X, LinkedIn, Threads)

```
Lancé DreamCut: descargador de video 100% local.

YouTube · TikTok · IG · X · Twitch
→ MP4/MP3 con calidades
→ Cola + canal + perfiles
→ Extensión Chrome + menú macOS

Sin webs raras. Todo en tu Mac.

github.com/giocrack890-creator/DreamCut
```

---

## Issue plantilla "Presentación" (opcional)

Puedes fijar un comentario en Discussions con el bloque de **Release / Announcement** de arriba.

---

## Checklist antes de publicar

- [ ] Cambiar `TU_USUARIO` por tu usuario de GitHub en todos los enlaces
- [ ] Añadir capturas en `docs/` y referenciarlas en el README
- [ ] Crear repo público y subir código (`git push`)
- [ ] Rellenar **About** con la descripción corta y los topics
- [ ] (Opcional) Crear Release `v1.0.0` pegando el texto de Announcement

# Extensión Chrome — Descargador YouTube / TikTok

Usa el **mismo servidor local** que la web (`./run.sh` en la raíz del proyecto).

## Instalación

1. **Genera los iconos** (solo la primera vez):

   ```bash
   python3 chrome-extension/generate_icons.py
   ```

2. **Arranca el servidor** (debe estar siempre encendido mientras uses la extensión):

   ```bash
   ./run.sh
   ```

3. En Chrome abre `chrome://extensions/`

4. Activa **Modo de desarrollador** (arriba a la derecha)

5. **Cargar descomprimida** → elige la carpeta:

   `~/Projects/video-downloader/chrome-extension`

6. Fija la extensión en la barra y ábrela en una pestaña de YouTube o TikTok: detectará el enlace automáticamente.

## Uso

1. Abre un video en YouTube o TikTok (o pega el enlace en el popup).
2. Pulsa **Analizar**.
3. Elige **Descargar** en MP4 o MP3.

Las descargas van a tu carpeta de Descargas de Chrome (subcarpeta `descargas/`).

## Notas

- Si ves *Servidor apagado*, ejecuta `./run.sh` de nuevo.
- La extensión solo habla con `http://127.0.0.1:8765` en tu máquina; no envía datos a internet aparte del análisis que ya hace `yt-dlp`.

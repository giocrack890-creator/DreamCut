#!/usr/bin/env bash
# Sube DreamCut a GitHub (ejecutar en TU Terminal, no dentro de Cursor)
set -euo pipefail
cd "$(dirname "$0")"

REPO_NAME="${1:-dreamcut}"

echo "→ Comprobando login en GitHub…"
gh auth status || {
  echo "❌ No hay sesión. Ejecuta: gh auth login"
  exit 1
}

echo "→ Preparando git…"
if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

git add -A
if git diff --cached --quiet; then
  echo "   (sin cambios nuevos para commitear)"
else
  git commit -m "$(cat <<'EOF'
DreamCut: descargador local de video multiplataforma

Panel web, extensión Chrome, cola de descargas, perfiles MP4/MP3,
modo canal YouTube, historial SQLite y menú macOS.
EOF
)"
fi

echo "→ Creando repo público: $REPO_NAME"
if gh repo view "$REPO_NAME" &>/dev/null; then
  echo "   El repo ya existe, solo hago push…"
  git remote remove origin 2>/dev/null || true
  gh repo set-default "$(gh api user -q .login)/$REPO_NAME"
  git remote add origin "https://github.com/$(gh api user -q .login)/${REPO_NAME}.git"
else
  gh repo create "$REPO_NAME" \
    --public \
    --source=. \
    --remote=origin \
    --description "DreamCut — Descargador local YouTube, TikTok, Instagram, X y Twitch. MP4/MP3, cola, extensión Chrome." \
    --push
  echo ""
  echo "✅ Listo: https://github.com/$(gh api user -q .login)/${REPO_NAME}"
  exit 0
fi

git push -u origin main
echo ""
echo "✅ Listo: https://github.com/$(gh api user -q .login)/${REPO_NAME}"

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

REMOTE="https://github.com/giocrack890-creator/DreamCut.git"

echo "→ Comprobando gh…"
gh auth status

# Repo git válido (recrear si está roto)
if ! git rev-parse --git-dir &>/dev/null; then
  echo "→ Inicializando git…"
  rm -rf .git 2>/dev/null || true
  git init
fi

git branch -M main 2>/dev/null || git checkout -b main

git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

echo "→ Añadiendo archivos…"
git add -A

if git diff --cached --quiet; then
  echo "   Nada nuevo que commitear."
else
  git commit -m "$(cat <<'EOF'
DreamCut: descargador local de video

Panel web, extensión Chrome, cola, perfiles, canal YouTube, historial y menú macOS.
EOF
)"
fi

# Si en GitHub creaste el repo con README
if git ls-remote origin main 2>/dev/null | grep -q .; then
  if ! git merge-base HEAD origin/main &>/dev/null 2>&1; then
    echo "→ Uniendo con el README de GitHub…"
    git pull origin main --rebase --allow-unrelated-histories || \
      git pull origin main --allow-unrelated-histories
  fi
fi

echo "→ Subiendo…"
git push -u origin main

echo ""
echo "✅ https://github.com/giocrack890-creator/DreamCut"

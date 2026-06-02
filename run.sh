#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -q -r requirements.txt

# Certificados SSL (macOS + Python.org)
export SSL_CERT_FILE="$(".venv/bin/python" -c "import certifi; print(certifi.where())")"
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"

exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8765

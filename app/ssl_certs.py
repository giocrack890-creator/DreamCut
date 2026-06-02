"""Fija certificados SSL en macOS (Python sin CA del sistema)."""
from __future__ import annotations

import os

try:
    import certifi
except ImportError:
    certifi = None  # type: ignore[assignment]

if certifi is not None:
    _ca = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", _ca)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", _ca)
    os.environ.setdefault("CURL_CA_BUNDLE", _ca)

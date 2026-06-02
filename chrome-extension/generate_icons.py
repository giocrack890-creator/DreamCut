#!/usr/bin/env python3
"""Genera iconos PNG para la extensión (solo stdlib)."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

ICONS = Path(__file__).parent / "icons"
COLOR = (108, 140, 255)


def _png(size: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    raw = b"".join(b"\x00" + bytes(COLOR) * size for _ in range(size))
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    ICONS.mkdir(exist_ok=True)
    for size in (16, 48, 128):
        path = ICONS / f"icon{size}.png"
        path.write_bytes(_png(size))
        print("wrote", path)


if __name__ == "__main__":
    main()

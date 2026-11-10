"""Imagens da interface carregadas como data URI, sem depender de rotas estáticas."""

import base64
from functools import lru_cache
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_MIME = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


@lru_cache(maxsize=None)
def data_uri(filename: str) -> str:
    path = ASSETS_DIR / filename
    if not path.is_file():
        return ""
    mime = _MIME.get(path.suffix.lower(), "application/octet-stream")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"

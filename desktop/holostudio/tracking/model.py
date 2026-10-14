"""Downloads the MediaPipe hand model once and keeps it on disk."""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path

from holostudio.config import HAND_LANDMARKER_FILE, HAND_LANDMARKER_URL


def ensure_hand_model(
    path: Path = HAND_LANDMARKER_FILE, url: str = HAND_LANDMARKER_URL, timeout: float = 300
) -> Path:
    """Returns the local model path, downloading it the first time only."""
    if path.exists() and path.stat().st_size > 0:
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".download")
    with urllib.request.urlopen(url, timeout=timeout) as response, temporary.open("wb") as file:
        while chunk := response.read(1 << 16):
            file.write(chunk)
    os.replace(temporary, path)
    return path

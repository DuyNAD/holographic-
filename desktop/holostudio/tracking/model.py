"""Downloads the MediaPipe hand model once and keeps it on disk."""

from __future__ import annotations

from pathlib import Path

from holostudio.config import HAND_LANDMARKER_FILE, HAND_LANDMARKER_URL
from holostudio.downloads import ensure_file


def ensure_hand_model(
    path: Path = HAND_LANDMARKER_FILE, url: str = HAND_LANDMARKER_URL, timeout: float = 300
) -> Path:
    """Returns the local model path, downloading it the first time only."""
    return ensure_file(path, url, timeout)

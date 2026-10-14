"""Downloads a model file once and keeps it on disk."""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path


def ensure_file(path: Path, url: str, timeout: float = 300) -> Path:
    """Returns the local path, downloading the file the first time only."""
    if path.exists() and path.stat().st_size > 0:
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".download")
    with urllib.request.urlopen(url, timeout=timeout) as response, temporary.open("wb") as file:
        while chunk := response.read(1 << 16):
            file.write(chunk)
    os.replace(temporary, path)
    return path

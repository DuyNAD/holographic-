"""Checks a file is a GLB 2.0 binary before it enters the library."""

from __future__ import annotations

import struct
from pathlib import Path

from holostudio.config import MAX_MODEL_FILE_BYTES

GLB_MAGIC = 0x46546C67  # "glTF"
GLB_VERSION = 2
GLB_HEADER_BYTES = 12


def validate_glb(path: Path, max_bytes: int = MAX_MODEL_FILE_BYTES) -> str | None:
    """Returns a user-facing error message, or None when the file is valid."""
    if path.suffix.lower() != ".glb":
        return "Chỉ hỗ trợ file GLB."
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return "File GLB phải nhỏ hơn hoặc bằng 25 MB."
        if size < GLB_HEADER_BYTES:
            return "File GLB không hợp lệ."
        with path.open("rb") as file:
            magic, version, declared_length = struct.unpack("<III", file.read(GLB_HEADER_BYTES))
    except OSError:
        return "Không thể đọc file GLB."

    if magic != GLB_MAGIC or version != GLB_VERSION or declared_length != size:
        return "File không phải GLB 2.0 hợp lệ."
    return None


def model_name_from_file(path: Path) -> str:
    name = path.name
    if name.lower().endswith(".glb"):
        name = name[:-4]
    return name.strip() or "Vật thể đã tải"

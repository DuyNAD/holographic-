import json
import struct

import pytest


def build_triangle_glb() -> bytes:
    """A minimal valid GLB 2.0 file: one triangle mesh."""
    positions = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 2, 0)
    document = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 3,
                "type": "VEC3",
                "min": [0, 0, 0],
                "max": [1, 2, 0],
            }
        ],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(positions)}],
        "buffers": [{"byteLength": len(positions)}],
    }
    json_chunk = json.dumps(document).encode()
    json_chunk += b" " * (-len(json_chunk) % 4)
    bin_chunk = positions + b"\0" * (-len(positions) % 4)
    body = (
        struct.pack("<II", len(json_chunk), 0x4E4F534A)
        + json_chunk
        + struct.pack("<II", len(bin_chunk), 0x004E4942)
        + bin_chunk
    )
    return struct.pack("<III", 0x46546C67, 2, 12 + len(body)) + body


@pytest.fixture
def glb_file(tmp_path):
    path = tmp_path / "robot.glb"
    path.write_bytes(build_triangle_glb())
    return path


@pytest.fixture(scope="session")
def base():
    """One offscreen Panda3D instance for the whole test session."""
    from panda3d.core import loadPrcFileData

    loadPrcFileData("", "window-type offscreen\nwin-size 1280 720\naudio-library-name null")
    from direct.showbase.ShowBase import ShowBase

    showbase = ShowBase()
    yield showbase
    showbase.destroy()

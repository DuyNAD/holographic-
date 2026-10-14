"""Loads a stored GLB into Panda3D, normalized to a common size and centred."""

from __future__ import annotations

from pathlib import Path

NORMALIZED_MODEL_SIZE = 1.6


class ModelLoadError(Exception):
    pass


def load_glb(path: Path):
    """Returns a Panda3D NodePath whose largest dimension is NORMALIZED_MODEL_SIZE."""
    import gltf
    from panda3d.core import NodePath

    try:
        model = gltf.load_model(str(path))
    except Exception as error:  # panda3d-gltf raises many different types
        raise ModelLoadError(str(error)) from error

    root = model if isinstance(model, NodePath) else NodePath(model)
    bounds = root.getTightBounds()
    if not bounds:
        raise ModelLoadError("Model does not contain renderable geometry.")

    low, high = bounds
    size = high - low
    largest = max(size.x, size.y, size.z)
    if largest <= 0:
        raise ModelLoadError("Model does not contain renderable geometry.")

    normalized = NodePath("normalized-model")
    root.reparentTo(normalized)
    root.setPos(-(low + high) / 2)
    normalized.setScale(NORMALIZED_MODEL_SIZE / largest)
    return normalized

"""Scene persistence as JSON on disk, with validation on load."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from .state import SceneObject, SceneState, clamp_scale, create_initial_scene

OBJECT_KINDS = {"box", "sphere", "cylinder", "model"}


def _vector(value) -> tuple[float, float, float] | None:
    if (
        isinstance(value, list)
        and len(value) == 3
        and all(
            isinstance(item, int | float) and not isinstance(item, bool) and math.isfinite(item)
            for item in value
        )
    ):
        return (float(value[0]), float(value[1]), float(value[2]))
    return None


def _parse_object(raw) -> SceneObject | None:
    if not isinstance(raw, dict):
        return None
    position = _vector(raw.get("position"))
    rotation = _vector(raw.get("rotation"))
    scale = raw.get("scale")
    kind = raw.get("kind")
    asset_id = raw.get("asset_id")
    valid = (
        isinstance(raw.get("id"), str)
        and isinstance(raw.get("name"), str)
        and kind in OBJECT_KINDS
        and isinstance(raw.get("color"), str)
        and position is not None
        and rotation is not None
        and isinstance(scale, int | float)
        and not isinstance(scale, bool)
        and math.isfinite(scale)
        and (kind != "model" or isinstance(asset_id, str))
    )
    if not valid:
        return None
    return SceneObject(
        id=raw["id"],
        name=raw["name"],
        kind=kind,
        color=raw["color"],
        position=position,
        rotation=rotation,
        scale=clamp_scale(float(scale)),
        asset_id=asset_id if kind == "model" else None,
    )


def load_scene(path: Path) -> SceneState:
    """Invalid or missing data falls back to the initial scene."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_objects = data["objects"]
        if not isinstance(raw_objects, list):
            return create_initial_scene()
        objects = [_parse_object(raw) for raw in raw_objects]
        if any(obj is None for obj in objects):
            return create_initial_scene()
        return SceneState(objects=tuple(objects))
    except (OSError, ValueError, KeyError, TypeError):
        return create_initial_scene()


def save_scene(scene: SceneState, path: Path) -> None:
    """Writes atomically so a crash never leaves a half-written scene file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "objects": [
            {
                "id": obj.id,
                "name": obj.name,
                "kind": obj.kind,
                "color": obj.color,
                "position": list(obj.position),
                "rotation": list(obj.rotation),
                "scale": obj.scale,
                **({"asset_id": obj.asset_id} if obj.asset_id else {}),
            }
            for obj in scene.objects
        ],
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)

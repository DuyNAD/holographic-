"""The user's hand measurements: bone lengths only, never images."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from math import dist
from pathlib import Path

from holostudio.config import DATA_DIR
from holostudio.tracking.types import Hand

PROFILE_FILE = DATA_DIR / "hand_profile.json"
PROFILE_VERSION = 1

# Every bone as (parent, child) MediaPipe landmark indexes, wrist outwards.
BONES: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (2, 3), (3, 4),  # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),  # index
    (0, 9), (9, 10), (10, 11), (11, 12),  # middle
    (0, 13), (13, 14), (14, 15), (15, 16),  # ring
    (0, 17), (17, 18), (18, 19), (19, 20),  # pinky
)  # fmt: skip


def bone_lengths(world: Hand) -> tuple[float, ...]:
    """Length of every bone in metres."""
    return tuple(dist(world[a], world[b]) for a, b in BONES)


@dataclass(frozen=True)
class HandProfile:
    bones: tuple[float, ...]  # metres, in BONES order
    # image_scale() of the hand while it was scanned: the "distance 1" reference.
    reference_scale: float


def save_profile(profile: HandProfile, path: Path = PROFILE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": PROFILE_VERSION,
        "bones": [round(length, 5) for length in profile.bones],
        "reference_scale": round(profile.reference_scale, 5),
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def load_profile(path: Path = PROFILE_FILE) -> HandProfile | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        bones = tuple(float(length) for length in data["bones"])
        scale = float(data["reference_scale"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    if data.get("version") != PROFILE_VERSION or len(bones) != len(BONES):
        return None
    if scale <= 0 or not all(0.003 < length < 0.2 for length in bones):
        return None
    return HandProfile(bones, scale)

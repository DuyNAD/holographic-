"""Coordinate conversions between camera landmarks, the screen, and the 3D view.

The camera preview is mirrored, so landmark x is flipped everywhere the user
sees it: the hand pointer, the HUD hit test, and the 3D ray.
"""

from __future__ import annotations

import math

from holostudio.tracking.types import Landmark

ScreenPoint = tuple[float, float]  # x right, y down, both in [0, 1] of the window


def landmark_to_screen(point: Landmark) -> ScreenPoint:
    return (1.0 - point.x, point.y)


def screen_to_ndc(point: ScreenPoint) -> tuple[float, float]:
    """Normalized device coordinates: x right, y up, both in [-1, 1]."""
    return (point[0] * 2 - 1, 1 - point[1] * 2)


def landmark_distance(first: Landmark, second: Landmark) -> float:
    return math.hypot(first.x - second.x, first.y - second.y)

"""Where the virtual hand is in the scene and what shape it has.

Placement: the palm sits on the camera ray through the palm in the (mirrored) camera
image, so the virtual hand covers the same part of the screen as the real hand covers
the camera image. Its distance from the 3D camera follows the real hand's distance
from the webcam: at the distance it was scanned it sits as deep as the scene centre,
twice as far away it sits twice as deep.

Shape: MediaPipe's 3D landmarks (metres) give each bone's direction; the lengths come
from the scanned profile, so the virtual hand keeps the user's proportions.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from holostudio.gestures.engine import TrackedHand
from holostudio.interaction.coordinates import ScreenPoint, landmark_to_screen
from holostudio.tracking.types import Landmark

from .depth import image_scale, relative_distance
from .profile import BONES, HandProfile

PALM = (0, 5, 9, 13, 17)  # wrist and knuckles: the palm centre is their average
# Distance range relative to the scan, so a bad frame cannot throw the hand away.
MIN_DISTANCE = 0.4
MAX_DISTANCE = 2.5


@dataclass(frozen=True)
class ViewRig:
    """The 3D camera, in scene coordinates."""

    origin: np.ndarray
    right: np.ndarray
    up: np.ndarray
    forward: np.ndarray  # into the screen
    ray: Callable[[ScreenPoint], np.ndarray]  # unit direction through a screen point
    tan_half_fov: float  # vertical
    reach: float  # camera to scene centre: the depth of a hand at its scanned distance


@dataclass(frozen=True)
class VirtualHand:
    track_id: int
    gesture: str
    joints: np.ndarray  # (21, 3) scene coordinates, MediaPipe landmark order
    units_per_metre: float  # scene units per metre of real hand (for thickness)
    distance: float  # distance now / distance at the scan


def units_per_metre(profile: HandProfile, rig: ViewRig) -> float:
    """Chosen so the hand at its scanned distance looks as big on screen as in the camera."""
    return profile.reference_scale * 2 * rig.reach * rig.tan_half_fov


def _average(points, indexes) -> np.ndarray:
    return np.mean([points[i] for i in indexes], axis=0)


def retarget(world: tuple[Landmark, ...], bones: tuple[float, ...]) -> np.ndarray:
    """The measured pose with every bone set to the profile's length (metres)."""
    source = np.array([(p.x, p.y, p.z) for p in world], dtype=float)
    joints = np.zeros_like(source)
    joints[0] = source[0]
    for (parent, child), length in zip(BONES, bones, strict=True):
        direction = source[child] - source[parent]
        norm = np.linalg.norm(direction)
        unit = direction / norm if norm > 1e-9 else np.zeros(3)
        joints[child] = joints[parent] + unit * length
    return joints


def solve(hand: TrackedHand, profile: HandProfile, rig: ViewRig) -> VirtualHand | None:
    if len(hand.world) != 21 or len(hand.landmarks) != 21:
        return None
    scale = hand.scale or image_scale(hand.landmarks, hand.world, hand.aspect)
    if scale is None:
        return None
    distance = min(
        max(relative_distance(scale, profile.reference_scale), MIN_DISTANCE), MAX_DISTANCE
    )

    palm = Landmark(*_average([(p.x, p.y, p.z) for p in hand.landmarks], PALM))
    ray = rig.ray(landmark_to_screen(palm))
    depth = rig.reach * distance  # along the view direction, so off-centre hands keep size
    anchor = rig.origin + ray * depth / max(float(ray @ rig.forward), 1e-3)

    shape = retarget(hand.world, profile.bones)
    shape -= _average(shape, PALM)
    k = units_per_metre(profile, rig)
    # MediaPipe world axes: x right and y down in the camera image, z away from the
    # webcam. The preview is a mirror, so image right is screen left.
    basis = np.stack([-rig.right, -rig.up, rig.forward])
    joints = anchor + (shape * k) @ basis
    return VirtualHand(hand.track_id, hand.gesture, joints, k, distance)

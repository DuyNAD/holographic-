"""Data passed from hand tracking to the gesture stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, NamedTuple

TrackingStatus = Literal["idle", "loading", "no-hand", "tracking", "error"]


class Landmark(NamedTuple):
    """Normalized camera coordinates: x, y in [0, 1] (unmirrored), z relative depth."""

    x: float
    y: float
    z: float


Hand = tuple[Landmark, ...]


@dataclass(frozen=True)
class HandFrame:
    hands: tuple[Hand, ...] = ()
    handedness: tuple[str, ...] = ()
    timestamp: float = 0.0
    # Hands of other people in view: ignored for control, drawn grey in the preview.
    other_hands: tuple[Hand, ...] = ()
    # The same hands in metres (MediaPipe world landmarks, centred on the hand), in the
    # same order as `hands`: the true 3D shape, used for the virtual hand.
    world_hands: tuple[Hand, ...] = ()
    # Camera frame width / height, to measure hand size without stretching.
    aspect: float = 16 / 9


@dataclass(frozen=True)
class TrackingState:
    status: TrackingStatus = "idle"
    message: str = "Bật camera để bắt đầu nhận diện tay."
    frame: HandFrame = field(default_factory=HandFrame)

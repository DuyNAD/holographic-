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


@dataclass(frozen=True)
class TrackingState:
    status: TrackingStatus = "idle"
    message: str = "Bật camera để bắt đầu nhận diện tay."
    frame: HandFrame = field(default_factory=HandFrame)

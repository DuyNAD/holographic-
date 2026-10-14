"""Data passed from hand tracking to the gesture stage."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal, NamedTuple

TrackingStatus = Literal["idle", "loading", "no-hand", "tracking", "error"]
DesignerStatus = Literal["unset", "enrolling", "pending", "locked", "absent", "unavailable"]


class Landmark(NamedTuple):
    """Normalized camera coordinates: x, y in [0, 1] (unmirrored), z relative depth."""

    x: float
    y: float
    z: float


Hand = tuple[Landmark, ...]


class FaceBox(NamedTuple):
    """A face rectangle in normalized camera coordinates (unmirrored)."""

    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True)
class DesignerInfo:
    status: DesignerStatus = "unset"
    message: str = "Chưa chọn người thiết kế"
    face: FaceBox | None = None
    other_faces: tuple[FaceBox, ...] = ()

    @property
    def locked(self) -> bool:
        return self.status == "locked"

    @property
    def pending(self) -> bool:
        """A face was recorded and waits for the user to confirm it."""
        return self.status == "pending"


@dataclass(frozen=True)
class HandFrame:
    hands: tuple[Hand, ...] = ()
    handedness: tuple[str, ...] = ()
    timestamp: float = 0.0
    # For each hand: does it belong to the designer? Empty when unknown.
    designer_hands: tuple[bool, ...] = ()


@dataclass(frozen=True)
class TrackingState:
    status: TrackingStatus = "idle"
    message: str = "Bật camera để bắt đầu nhận diện tay."
    frame: HandFrame = field(default_factory=HandFrame)
    designer: DesignerInfo = field(default_factory=DesignerInfo)

    def designer_only(self) -> TrackingState:
        """The same frame with only the designer's hands left in it."""
        frame = self.frame
        keep = [i for i, mine in enumerate(frame.designer_hands) if mine]
        hands = tuple(frame.hands[i] for i in keep)
        handedness = tuple(frame.handedness[i] for i in keep if i < len(frame.handedness))
        return replace(
            self,
            status="tracking" if hands else "no-hand",
            frame=replace(
                frame, hands=hands, handedness=handedness, designer_hands=(True,) * len(hands)
            ),
        )

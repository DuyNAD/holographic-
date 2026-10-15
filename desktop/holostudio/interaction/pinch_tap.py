"""Pinch taps: each new pinch counts once, like a mouse click.

Used while picking objects to group: pinching on an object toggles it, and holding
the pinch does not toggle it again.
"""

from __future__ import annotations

from holostudio.gestures.engine import StableGesture

from .coordinates import ScreenPoint, landmark_to_screen


class PinchTaps:
    def __init__(self) -> None:
        self._pinching: set[int] = set()

    def update(self, gestures: tuple[StableGesture, ...]) -> list[ScreenPoint]:
        """Screen points of pinches that started since the last call."""
        now = {g.track_id for g in gestures if g.name == "pinch"}
        started = [
            landmark_to_screen(g.index_tip)
            for g in gestures
            if g.name == "pinch" and g.track_id not in self._pinching
        ]
        self._pinching = now
        return started

    def reset(self) -> None:
        self._pinching = set()

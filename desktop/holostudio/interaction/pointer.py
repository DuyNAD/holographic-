"""The hand pointer: finds the HUD button under the pointing finger and presses it."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from holostudio.gestures.engine import StableGesture

from .coordinates import ScreenPoint, landmark_to_screen
from .dwell import DwellState, advance_dwell


@dataclass(frozen=True)
class PointerMark:
    """One cursor to draw for each hand that shows a gesture."""

    position: ScreenPoint
    gesture: str
    is_pointer: bool


@dataclass(frozen=True)
class PointerFrame:
    marks: tuple[PointerMark, ...]
    hover: str | None
    progress: float
    pressed: str | None


class HandPointer:
    def __init__(self, target_at: Callable[[ScreenPoint], str | None]) -> None:
        """`target_at` returns the id of an enabled HUD button at a screen point."""
        self._target_at = target_at
        self._dwell: DwellState[str] = DwellState()

    def update(self, gestures: tuple[StableGesture, ...], now: float) -> PointerFrame:
        pointer = next((g for g in gestures if g.name == "point"), None)
        position = landmark_to_screen(pointer.index_tip) if pointer else None
        target = self._target_at(position) if position else None

        step = advance_dwell(self._dwell, target, now)
        self._dwell = step.state

        marks = tuple(
            PointerMark(landmark_to_screen(g.index_tip), g.name, g is pointer)
            for g in gestures
            if len(g.landmarks) > 8
        )
        held = step.state.target  # stays set during a brief slip off the button
        return PointerFrame(marks, held, step.progress, held if step.fire else None)

"""Dwell-to-press: holding the pointer on one target presses it once."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from holostudio.config import DWELL_SECONDS

T = TypeVar("T")

# A pointer that slips off its button for less than this keeps its progress,
# so hand jitter at a button's edge does not restart the countdown.
GRACE_SECONDS = 0.25


@dataclass(frozen=True)
class DwellState(Generic[T]):
    target: T | None = None
    started_at: float = 0.0
    fired: bool = False
    last_seen: float = 0.0


@dataclass(frozen=True)
class DwellStep(Generic[T]):
    state: DwellState[T]
    progress: float
    fire: bool


def advance_dwell(
    state: DwellState[T],
    target: T | None,
    now: float,
    duration: float = DWELL_SECONDS,
    grace: float = GRACE_SECONDS,
) -> DwellStep[T]:
    """The same target only fires again after the pointer leaves it."""
    if target != state.target:
        holding = state.target is not None and now - state.last_seen < grace
        if holding:
            return DwellStep(state, _progress(state, now, duration), False)
        if target is None:
            return DwellStep(DwellState(), 0.0, False)
        return DwellStep(DwellState(target, now, False, now), 0.0, False)

    if target is None:
        return DwellStep(state, 0.0, False)
    seen = DwellState(target, state.started_at, state.fired, now)
    if state.fired:
        return DwellStep(seen, 1.0, False)

    progress = _progress(state, now, duration)
    if progress < 1.0:
        return DwellStep(seen, progress, False)
    return DwellStep(DwellState(target, state.started_at, True, now), 1.0, True)


def _progress(state: DwellState, now: float, duration: float) -> float:
    if state.fired:
        return 1.0
    return min(1.0, (now - state.started_at) / duration)

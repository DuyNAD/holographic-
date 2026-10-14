"""Classifies one hand's landmarks into a gesture."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from holostudio.tracking.types import Hand, Landmark

GestureName = Literal["none", "point", "pinch", "fist", "open-palm"]

FINGER_JOINTS = ((6, 8), (10, 12), (14, 16), (18, 20))  # (pip, tip) for index..pinky
PINCH_RATIO = 0.38
# Once pinching, the fingers may open this far before the pinch counts as released.
# The gap between entering and leaving (hysteresis) stops point/pinch flicker.
PINCH_RELEASE_RATIO = 0.5
EXTENDED_RATIO = 1.12
# In a fist the index tip curls back to about the height of its knuckle (MCP).
# A pinch keeps the index tip beyond the knuckle, so the two are told apart even
# though the thumb tip touches the index finger in both.
INDEX_FOLDED_RATIO = 1.05


@dataclass(frozen=True)
class Observation:
    name: GestureName
    confidence: float


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def _distance(a: Landmark, b: Landmark) -> float:
    return math.dist(a, b)


def _finger_extended(hand: Hand, pip: int, tip: int) -> bool:
    wrist = hand[0]
    return _distance(wrist, hand[tip]) > _distance(wrist, hand[pip]) * EXTENDED_RATIO


def _index_folded(hand: Hand) -> bool:
    wrist = hand[0]
    return _distance(wrist, hand[8]) < _distance(wrist, hand[5]) * INDEX_FOLDED_RATIO


def detect_gesture(hand: Hand, current: GestureName = "none") -> Observation:
    """`current` is the hand's active gesture; it makes leaving a gesture a bit harder
    than entering it (hysteresis), which stops flicker at the boundary."""
    if len(hand) < 21:
        return Observation("none", 0.0)

    palm_size = _distance(hand[0], hand[9])
    if palm_size <= 1e-9:
        return Observation("none", 0.0)

    extended = [_finger_extended(hand, pip, tip) for pip, tip in FINGER_JOINTS]
    count = sum(extended)
    index_folded = _index_folded(hand)

    pinch_ratio = _distance(hand[4], hand[8]) / palm_size
    if not index_folded:
        if current == "pinch" and pinch_ratio < PINCH_RELEASE_RATIO:
            return Observation("pinch", max(0.6, _clamp01((0.45 - pinch_ratio) / 0.3)))
        if pinch_ratio < PINCH_RATIO:
            return Observation("pinch", _clamp01((0.45 - pinch_ratio) / 0.3))

    if count == 4:
        return Observation("open-palm", 1.0)
    if extended[0] and not any(extended[1:]):
        return Observation("point", 1.0)
    # A fist: index and middle curled; one loose finger (often the pinky) is allowed,
    # and a held fist tolerates one more while the hand moves.
    if not extended[0] and not extended[1] and count <= (2 if current == "fist" else 1):
        return Observation("fist", 1.0)
    return Observation("none", _clamp01(1 - count / 4))

"""Turns tracking frames into stable, per-hand gestures."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import permutations

from holostudio.tracking.types import Hand, Landmark, TrackingState

from .classifier import GestureName, detect_gesture
from .filters import OneEuroHandFilter
from .state_machine import GestureMachine, advance

GESTURE_LABELS: dict[str, str] = {
    "point": "Trỏ",
    "pinch": "Chụm",
    "fist": "Nắm tay",
    "open-palm": "Mở tay",
}


@dataclass(frozen=True)
class StableGesture:
    hand_index: int
    handedness: str
    name: GestureName
    confidence: float
    landmarks: Hand
    # Stays the same for one physical hand across frames, whatever order MediaPipe uses.
    track_id: int = 0

    @property
    def index_tip(self):
        return self.landmarks[8]


# Max wrist movement between frames (normalized image units) for "the same hand".
MATCH_DISTANCE = 0.25


@dataclass
class _HandTrack:
    id: int
    filter: OneEuroHandFilter
    machine: GestureMachine
    wrist: Landmark


def _match(tracks: list[_HandTrack], hands: tuple[Hand, ...]) -> list[_HandTrack | None]:
    """Pairs each detected hand with the previous track whose wrist is nearest.

    MediaPipe can list the hands in any order and its Left/Right labels flicker,
    so hands are followed by position instead.
    """
    best: list[_HandTrack | None] = [None] * len(hands)
    best_cost = math.inf
    candidates = [*tracks, *([None] * len(hands))]
    for chosen in permutations(candidates, len(hands)):
        cost = 0.0
        for hand, track in zip(hands, chosen, strict=True):
            if track is None:
                cost += MATCH_DISTANCE
                continue
            distance = math.dist(hand[0][:2], track.wrist[:2])
            if distance > MATCH_DISTANCE:
                cost = math.inf
                break
            cost += distance
        if cost < best_cost:
            best, best_cost = list(chosen), cost
    return best


class GestureEngine:
    def __init__(self) -> None:
        self._tracks: list[_HandTrack] = []
        self._next_id = 1
        self._last_timestamp: float | None = None
        self.gestures: tuple[StableGesture, ...] = ()

    def update(self, tracking: TrackingState) -> tuple[StableGesture, ...]:
        if tracking.status != "tracking":
            self._tracks = []
            self._last_timestamp = None
            self.gestures = ()
            return self.gestures

        frame = tracking.frame
        if frame.timestamp == self._last_timestamp:
            return self.gestures  # same camera frame as last render tick
        self._last_timestamp = frame.timestamp

        hands = frame.hands[:4]
        matched = _match(self._tracks, hands)
        tracks: list[_HandTrack] = []
        gestures: list[StableGesture] = []

        for index, (hand, track) in enumerate(zip(hands, matched, strict=True)):
            if track is None:
                track = _HandTrack(self._next_id, OneEuroHandFilter(), GestureMachine(), hand[0])
                self._next_id += 1
            landmarks = track.filter(hand, frame.timestamp)
            observation = detect_gesture(landmarks, track.machine.current)
            track.machine = advance(track.machine, observation)
            track.wrist = hand[0]
            tracks.append(track)
            if track.machine.current != "none":
                handedness = frame.handedness[index] if index < len(frame.handedness) else ""
                gestures.append(
                    StableGesture(
                        index,
                        handedness,
                        track.machine.current,
                        track.machine.confidence,
                        landmarks,
                        track.id,
                    )
                )

        self._tracks = tracks
        self.gestures = tuple(gestures)
        return self.gestures

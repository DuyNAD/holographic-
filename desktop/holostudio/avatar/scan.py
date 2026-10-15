"""Scanning the hand: hold an open palm still inside the guide box for a moment."""

from __future__ import annotations

from dataclasses import dataclass
from math import dist
from statistics import median
from typing import Literal

from holostudio.gestures.engine import TrackedHand

from .depth import image_scale
from .profile import BONES, HandProfile, bone_lengths

# The guide box in camera image coordinates (0..1); symmetric, so the same after mirroring.
SCAN_BOX = (0.28, 0.12, 0.72, 0.92)  # left, top, right, bottom
SCAN_FRAMES = 30  # about one second at 30 fps
STILL_DISTANCE = 0.04  # how far the wrist may drift (image heights) while scanning

ScanPhase = Literal["waiting", "scanning", "done"]

MESSAGES = {
    "no-hand": "Đưa bàn tay vào khung",
    "outside": "Đưa cả bàn tay vào trong khung",
    "closed": "Xòe thẳng bàn tay, lòng bàn tay hướng về camera",
    "moving": "Giữ yên tay…",
    "scanning": "Đang quét… giữ yên tay",
    "done": "Đã quét xong bàn tay",
}


@dataclass(frozen=True)
class ScanStatus:
    phase: ScanPhase
    progress: float  # 0..1
    message: str


def inside_box(hand: TrackedHand) -> bool:
    left, top, right, bottom = SCAN_BOX
    return all(left <= p.x <= right and top <= p.y <= bottom for p in hand.landmarks)


class HandScan:
    def __init__(self) -> None:
        self._samples: list[tuple[float, ...]] = []
        self._scales: list[float] = []
        self._anchor: tuple[float, float] | None = None
        self.profile: HandProfile | None = None
        self.status = ScanStatus("waiting", 0.0, MESSAGES["no-hand"])

    def update(self, hands: tuple[TrackedHand, ...]) -> ScanStatus:
        if self.profile is not None:
            return self.status
        hand = hands[0] if hands else None
        problem = self._problem(hand)
        scale = None
        if problem is None:
            scale = hand.scale or image_scale(hand.landmarks, hand.world, hand.aspect)
        if problem is None and scale is None:
            problem = "closed"
        if problem is None:
            wrist = (hand.landmarks[0].x, hand.landmarks[0].y)
            if self._anchor is None:
                self._anchor = wrist
            elif dist(self._anchor, wrist) > STILL_DISTANCE:
                problem = "moving"
        if problem is not None:
            self._samples.clear()
            self._scales.clear()
            self._anchor = None
            self.status = ScanStatus("waiting", 0.0, MESSAGES[problem])
            return self.status

        self._samples.append(bone_lengths(hand.world))
        self._scales.append(scale)
        if len(self._samples) < SCAN_FRAMES:
            progress = len(self._samples) / SCAN_FRAMES
            self.status = ScanStatus("scanning", progress, MESSAGES["scanning"])
            return self.status
        bones = tuple(median(s[i] for s in self._samples) for i in range(len(BONES)))
        self.profile = HandProfile(bones, median(self._scales))
        self.status = ScanStatus("done", 1.0, MESSAGES["done"])
        return self.status

    @staticmethod
    def _problem(hand: TrackedHand | None) -> str | None:
        if hand is None or len(hand.world) != len(hand.landmarks):
            return "no-hand"
        if not inside_box(hand):
            return "outside"
        if hand.gesture != "open-palm":
            return "closed"
        return None

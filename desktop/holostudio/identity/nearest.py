"""Only the user nearest the camera controls the app.

The nearest person is the body with the widest shoulders in the image. Hands are
kept when they belong to that body (their wrist is at one of its wrists). When no
body is visible (for example when sitting very close to the camera), the biggest
hands are kept, because they are the closest ones.

Body pose runs on its own thread, so hand tracking stays at the camera frame rate;
hands are matched to the most recent bodies (a frame or two old at most).
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass

import numpy as np

from holostudio.tracking.types import Hand

from .bodies import Body, PoseDetector, ensure_pose_model, hand_owner

# Another person must be this much bigger (closer) than the current user…
SWITCH_RATIO = 1.15
# …for this long before control moves to them, so two people standing at about
# the same distance never make control jump back and forth.
SWITCH_SECONDS = 0.5
# Max nose movement between frames for "the same person".
FOLLOW_DISTANCE = 0.15
# Without a matching body, a hand is kept if it is at least this big compared
# with the biggest hand in view.
PALM_KEEP_RATIO = 0.7


def palm_size(hand: Hand) -> float:
    """Wrist to middle knuckle: bigger means closer to the camera."""
    return math.dist(hand[0][:2], hand[9][:2]) if len(hand) > 9 else 0.0


class NearestUser:
    """Follows the person nearest the camera, without flickering between people."""

    def __init__(self) -> None:
        self._nose: tuple[float, float] | None = None
        self._challenger_since: float | None = None

    def update(self, bodies: list[Body], timestamp: float) -> int | None:
        if not bodies:
            self._nose = None
            self._challenger_since = None
            return None

        biggest = max(range(len(bodies)), key=lambda i: bodies[i].size)
        current = self._follow(bodies)
        if current is None:
            chosen = biggest
            self._challenger_since = None
        elif biggest != current and bodies[biggest].size > bodies[current].size * SWITCH_RATIO:
            if self._challenger_since is None:
                self._challenger_since = timestamp
            if timestamp - self._challenger_since >= SWITCH_SECONDS:
                chosen = biggest
                self._challenger_since = None
            else:
                chosen = current
        else:
            chosen = current
            self._challenger_since = None

        self._nose = bodies[chosen].nose
        return chosen

    def _follow(self, bodies: list[Body]) -> int | None:
        if self._nose is None:
            return None
        index = min(range(len(bodies)), key=lambda i: math.dist(bodies[i].nose, self._nose))
        return index if math.dist(bodies[index].nose, self._nose) <= FOLLOW_DISTANCE else None


def nearest_hand_mask(
    bodies: list[Body], nearest: int | None, hands: tuple[Hand, ...]
) -> tuple[bool, ...]:
    """Which detected hands belong to the nearest user."""
    if not hands:
        return ()
    biggest = max(palm_size(hand) for hand in hands)
    mask = []
    for hand in hands:
        owner = hand_owner(bodies, hand) if bodies else None
        if owner is not None:
            mask.append(owner == nearest)  # attached to a body: only the nearest user's
        else:
            # No body to match (none visible, or the wrist is out of frame): keep it
            # only if it is about as big as the closest hand.
            mask.append(palm_size(hand) >= biggest * PALM_KEEP_RATIO)
    return tuple(mask)


@dataclass(frozen=True)
class _Latest:
    bodies: tuple[Body, ...] = ()
    nearest: int | None = None


class NearestUserFilter:
    """Pose on its own thread; `mask` answers at once from the latest bodies."""

    def __init__(self, poses: PoseDetector) -> None:
        self._poses = poses
        self._nearest = NearestUser()
        self._guard = threading.Lock()
        self._wake = threading.Condition(self._guard)
        self._pending: tuple[np.ndarray, float] | None = None
        self._latest = _Latest()
        self._stop = False
        self._thread = threading.Thread(target=self._run, name="nearest-user", daemon=True)
        self._thread.start()

    def mask(
        self, image: np.ndarray, timestamp: float, hands: tuple[Hand, ...]
    ) -> tuple[bool, ...]:
        with self._wake:
            self._pending = (image, timestamp)
            self._wake.notify()
            latest = self._latest
        return nearest_hand_mask(list(latest.bodies), latest.nearest, hands)

    def _run(self) -> None:
        while True:
            with self._wake:
                while self._pending is None and not self._stop:
                    self._wake.wait()
                if self._stop:
                    return
                image, timestamp = self._pending
                self._pending = None
            try:
                bodies = self._poses.detect(image, timestamp)
            except Exception:
                continue  # one bad frame must not stop the filter
            nearest = self._nearest.update(bodies, timestamp)
            with self._guard:
                self._latest = _Latest(tuple(bodies), nearest)

    def close(self) -> None:
        with self._wake:
            self._stop = True
            self._wake.notify()
        self._thread.join(timeout=2)
        self._poses.close()


def default_nearest_filter() -> NearestUserFilter:
    return NearestUserFilter(PoseDetector(ensure_pose_model()))

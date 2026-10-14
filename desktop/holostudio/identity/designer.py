"""Locks hand control to one person: the designer.

Pressing "Người thiết kế" records the face nearest the camera. That person is
then a candidate: they are followed like the designer, but nothing is locked until
the user confirms (or picks again / cancels). Once confirmed, the designer is
followed from frame to frame by their body and re-checked by face a few times per
second. Only hands attached to the designer's body are used. The designer stays
locked for the whole session, until the button is pressed again.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np

from holostudio.tracking.types import Hand

from .bodies import Body, face_owner, hand_owner
from .faces import SAME_PERSON_SIMILARITY, Face, cosine_similarity, nearest_face

DesignerStatus = Literal["unset", "enrolling", "pending", "locked", "absent"]

ENROLL_SAMPLES = 5  # face fingerprints averaged when recording the designer
ENROLL_TIMEOUT_SECONDS = 4.0
VERIFY_INTERVAL_SECONDS = 0.3  # how often the designer's face is re-checked
TRACK_DISTANCE = 0.15  # max nose movement between frames for "the same body"
ABSENT_SECONDS = 0.7  # designer unseen this long = away from the camera
CONFIRM_TIMEOUT_SECONDS = 20.0  # an unconfirmed candidate is dropped after this

STATUS_MESSAGES: dict[DesignerStatus, str] = {
    "unset": "Chưa chọn người thiết kế",
    "enrolling": "Đang ghi nhận mặt…",
    "pending": "Chờ xác nhận người thiết kế",
    "locked": "Đã khóa người thiết kế",
    "absent": "Không thấy người thiết kế",
}


@dataclass(frozen=True)
class IdentityFrame:
    faces: list[Face]
    bodies: list[Body]
    timestamp: float
    fingerprint: Callable[[Face], np.ndarray]  # computed only when needed (costly)


@dataclass(frozen=True)
class DesignerView:
    status: DesignerStatus
    message: str
    body: int | None  # index into the frame's bodies, when the designer is visible
    face: Face | None  # the designer's face box, for the camera preview
    other_faces: tuple[Face, ...] = ()


class DesignerLock:
    def __init__(self) -> None:
        self.status: DesignerStatus = "unset"
        self.message = STATUS_MESSAGES["unset"]
        self._fingerprint: np.ndarray | None = None
        self._samples: list[np.ndarray] = []
        self._enroll_started = 0.0
        self._nose: tuple[float, float] | None = None
        self._last_seen = 0.0
        self._last_verified = -math.inf
        # False after a face check rejected the tracked body: until the designer's
        # face is seen again, position alone is not trusted.
        self._trusted = False
        # A recorded face only becomes the designer once the user confirms it.
        self._confirmed = False
        self._pending_since = 0.0
        # The designer before "choose again", restored if the user cancels.
        self._previous: tuple[np.ndarray, tuple[float, float] | None] | None = None

    @property
    def locked(self) -> bool:
        return self._confirmed and self.status in ("locked", "absent")

    @property
    def pending(self) -> bool:
        return self.status == "pending"

    def request_enrollment(self, now: float) -> None:
        """Record the person nearest the camera as a candidate for designer."""
        if self._confirmed and self._fingerprint is not None:
            self._previous = (self._fingerprint, self._nose)
        self.status = "enrolling"
        self.message = STATUS_MESSAGES["enrolling"]
        self._fingerprint = None
        self._confirmed = False
        self._samples = []
        self._enroll_started = now
        self._nose = None

    def confirm(self) -> bool:
        """The user accepts the candidate: lock them as the designer."""
        if self.status != "pending":
            return False
        self._confirmed = True
        self._previous = None
        self.status = "locked"
        self.message = STATUS_MESSAGES["locked"]
        return True

    def cancel(self) -> None:
        """Drop the candidate; the earlier designer (if any) stays in charge."""
        if self.status not in ("pending", "enrolling"):
            return
        if self._previous is not None:
            self._fingerprint, self._nose = self._previous
            self._previous = None
            self._confirmed = True
            self._trusted = False  # re-find the designer by face before trusting position
            self._last_verified = -math.inf
            self.status = "absent"
        else:
            self._fingerprint = None
            self._nose = None
            self.status = "unset"
        self.message = STATUS_MESSAGES[self.status]

    def update(self, frame: IdentityFrame) -> DesignerView:
        if self.status == "enrolling":
            return self._enroll(frame)
        if self.status == "unset":
            return DesignerView("unset", self.message, None, None, tuple(frame.faces))
        return self._follow(frame)

    # --- recording the designer ----------------------------------------------

    def _enroll(self, frame: IdentityFrame) -> DesignerView:
        face = nearest_face(frame.faces)
        if face is None:
            if frame.timestamp - self._enroll_started > ENROLL_TIMEOUT_SECONDS:
                self.status = "unset"
                self.message = "Không thấy mặt · chọn lại"
            return DesignerView(self.status, self.message, None, None, ())

        self._samples.append(frame.fingerprint(face))
        body = face_owner(frame.bodies, face)
        if body is not None:
            self._nose = frame.bodies[body].nose
        others = tuple(f for f in frame.faces if f is not face)

        if len(self._samples) < ENROLL_SAMPLES:
            progress = f"{STATUS_MESSAGES['enrolling']} {len(self._samples)}/{ENROLL_SAMPLES}"
            return DesignerView("enrolling", progress, None, face, others)

        average = np.mean([s / np.linalg.norm(s) for s in self._samples], axis=0)
        self._fingerprint = average / np.linalg.norm(average)
        self._samples = []
        self._last_seen = frame.timestamp
        self._last_verified = frame.timestamp
        self._trusted = True
        self._pending_since = frame.timestamp
        self.status = "pending"
        self.message = STATUS_MESSAGES["pending"]
        return DesignerView("pending", self.message, body, face, others)

    # --- following the designer ----------------------------------------------

    def _follow(self, frame: IdentityFrame) -> DesignerView:
        if not self._confirmed and frame.timestamp - self._pending_since > CONFIRM_TIMEOUT_SECONDS:
            self.cancel()
            if self.status == "unset":
                return DesignerView("unset", self.message, None, None, tuple(frame.faces))
        body = self._nearest_body(frame.bodies)
        must_verify = (
            body is None
            or not self._trusted
            or frame.timestamp - self._last_verified >= VERIFY_INTERVAL_SECONDS
        )
        designer_face = None

        if must_verify and frame.faces:
            match = self._matching_face(frame)
            self._last_verified = frame.timestamp
            if match is not None:
                designer_face = match
                owner = face_owner(frame.bodies, match)
                body = owner if owner is not None else body
                self._trusted = True
            elif body is not None and self._face_of(frame, body) is not None:
                body = None  # someone else is standing where the designer was
                self._trusted = False
        if not self._trusted and designer_face is None:
            body = None

        if body is not None:
            self._nose = frame.bodies[body].nose
            self._last_seen = frame.timestamp
            if designer_face is None:
                designer_face = self._face_of(frame, body)
            self.status = "locked"
        elif frame.timestamp - self._last_seen > ABSENT_SECONDS:
            self.status = "absent"
        if not self._confirmed:
            self.status = "pending"  # followed like the designer, but not locked yet
        self.message = STATUS_MESSAGES[self.status]

        others = tuple(f for f in frame.faces if f is not designer_face)
        return DesignerView(
            self.status, self.message, body, designer_face if body is not None else None, others
        )

    def _nearest_body(self, bodies: list[Body]) -> int | None:
        if self._nose is None or not bodies:
            return None
        index = min(range(len(bodies)), key=lambda i: math.dist(bodies[i].nose, self._nose))
        return index if math.dist(bodies[index].nose, self._nose) <= TRACK_DISTANCE else None

    def _matching_face(self, frame: IdentityFrame) -> Face | None:
        assert self._fingerprint is not None
        scored = [
            (cosine_similarity(self._fingerprint, frame.fingerprint(face)), face)
            for face in frame.faces
        ]
        similarity, face = max(scored, key=lambda pair: pair[0])
        return face if similarity >= SAME_PERSON_SIMILARITY else None

    @staticmethod
    def _face_of(frame: IdentityFrame, body: int) -> Face | None:
        return next((f for f in frame.faces if face_owner(frame.bodies, f) == body), None)


def designer_hand_mask(
    bodies: list[Body], designer_body: int | None, hands: tuple[Hand, ...]
) -> tuple[bool, ...]:
    """Which detected hands belong to the designer."""
    if designer_body is None:
        return tuple(False for _ in hands)
    return tuple(hand_owner(bodies, hand) == designer_body for hand in hands)

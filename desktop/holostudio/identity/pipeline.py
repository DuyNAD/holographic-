"""Face + body detection on its own thread, next to hand tracking.

Hand tracking must stay at the camera's frame rate, so identity work (body pose
and faces, ~25 ms per frame) runs in parallel on the newest camera frame. Hands
are matched to the most recent bodies, which are at most a frame or two old;
HAND_TO_WRIST leaves room for that.
"""

from __future__ import annotations

import threading

import numpy as np

from holostudio.tracking.types import DesignerInfo, FaceBox, Hand

from .bodies import Body, PoseDetector, ensure_pose_model
from .designer import DesignerLock, DesignerView, IdentityFrame, designer_hand_mask
from .faces import Face, FaceIdentifier, ensure_face_models


def _box(face: Face) -> FaceBox:
    return FaceBox(face.x, face.y, face.w, face.h)


def to_info(view: DesignerView) -> DesignerInfo:
    return DesignerInfo(
        status=view.status,
        message=view.message,
        face=_box(view.face) if view.face is not None else None,
        other_faces=tuple(_box(face) for face in view.other_faces),
    )


class IdentityPipeline:
    def __init__(self, faces: FaceIdentifier, poses: PoseDetector) -> None:
        self._faces = faces
        self._poses = poses
        self.lock = DesignerLock()
        self._guard = threading.Lock()
        self._wake = threading.Condition(self._guard)
        self._pending: tuple[np.ndarray, float] | None = None
        self._enroll_at: float | None = None
        self._decision: str | None = None  # "confirm" or "cancel", applied on the thread
        self._bodies: list[Body] = []
        self._designer_body: int | None = None
        self._info = DesignerInfo()
        self._stop = False
        self._thread = threading.Thread(target=self._run, name="identity", daemon=True)
        self._thread.start()

    def request_enrollment(self, now: float) -> None:
        with self._guard:
            self._enroll_at = now
            self._decision = None

    def confirm(self) -> None:
        """Lock the candidate shown to the user."""
        with self._guard:
            self._decision = "confirm"

    def cancel(self) -> None:
        """Drop the candidate; the previous designer (if any) stays."""
        with self._guard:
            self._decision = "cancel"

    def process(
        self, image: np.ndarray, timestamp: float, hands: tuple[Hand, ...]
    ) -> tuple[tuple[bool, ...], DesignerInfo]:
        """Hands the frame to the identity thread and returns ownership from the
        latest identity result (never waits for face or body detection)."""
        with self._wake:
            self._pending = (image, timestamp)
            self._wake.notify()
            bodies, body, info = self._bodies, self._designer_body, self._info
        return designer_hand_mask(bodies, body, hands), info

    def _run(self) -> None:
        while True:
            with self._wake:
                while self._pending is None and not self._stop:
                    self._wake.wait()
                if self._stop:
                    return
                image, timestamp = self._pending
                self._pending = None
                enroll_at, self._enroll_at = self._enroll_at, None
                decision, self._decision = self._decision, None

            if enroll_at is not None:
                self.lock.request_enrollment(enroll_at)
            if decision == "confirm":
                self.lock.confirm()
            elif decision == "cancel":
                self.lock.cancel()
            try:
                bodies = self._poses.detect(image, timestamp)
                faces = self._faces.detect(image)
                view = self.lock.update(
                    IdentityFrame(
                        faces=faces,
                        bodies=bodies,
                        timestamp=timestamp,
                        fingerprint=lambda face, image=image: self._faces.fingerprint(image, face),
                    )
                )
            except Exception:
                continue  # one bad frame must not stop identity tracking
            with self._guard:
                self._bodies, self._designer_body, self._info = bodies, view.body, to_info(view)

    def close(self) -> None:
        with self._wake:
            self._stop = True
            self._wake.notify()
        self._thread.join(timeout=2)
        self._poses.close()


def default_identity_pipeline() -> IdentityPipeline:
    detector_path, recognizer_path = ensure_face_models()
    return IdentityPipeline(
        FaceIdentifier(detector_path, recognizer_path), PoseDetector(ensure_pose_model())
    )

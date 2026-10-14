"""Face detection (YuNet) and face recognition (SFace), both from OpenCV.

MediaPipe can find faces but cannot tell people apart; SFace turns a face into a
128-number "fingerprint" so the same person can be recognised again. Everything
runs on this machine, and fingerprints only live in memory for the session.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from holostudio import config
from holostudio.downloads import ensure_file

DETECTION_SCORE = 0.8
# SFace's published cosine threshold for "same person".
SAME_PERSON_SIMILARITY = 0.363


@dataclass(frozen=True)
class Face:
    """A detected face; box and points are normalized to the frame (0..1)."""

    x: float
    y: float
    w: float
    h: float
    score: float
    raw: np.ndarray  # YuNet row in pixels, needed to align the face for SFace

    @property
    def centre(self) -> tuple[float, float]:
        return (self.x + self.w / 2, self.y + self.h / 2)

    @property
    def area(self) -> float:
        """Bigger means closer to the camera."""
        return self.w * self.h

    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        return self.x - margin * self.w <= x <= self.x + self.w * (
            1 + margin
        ) and self.y - margin * self.h <= y <= self.y + self.h * (1 + margin)


def ensure_face_models() -> tuple[Path, Path]:
    return (
        ensure_file(config.FACE_DETECTOR_FILE, config.FACE_DETECTOR_URL),
        ensure_file(config.FACE_RECOGNIZER_FILE, config.FACE_RECOGNIZER_URL),
    )


def cosine_similarity(first: np.ndarray, second: np.ndarray) -> float:
    a, b = first.ravel(), second.ravel()
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


class FaceIdentifier:
    def __init__(self, detector_path: Path, recognizer_path: Path) -> None:
        import cv2

        self._detector = cv2.FaceDetectorYN.create(
            str(detector_path), "", (320, 320), DETECTION_SCORE, 0.3, 5000
        )
        self._recognizer = cv2.FaceRecognizerSF.create(str(recognizer_path), "")
        self._size: tuple[int, int] | None = None

    def detect(self, image_bgr: np.ndarray) -> list[Face]:
        height, width = image_bgr.shape[:2]
        if self._size != (width, height):
            self._detector.setInputSize((width, height))
            self._size = (width, height)
        _ok, rows = self._detector.detect(image_bgr)
        if rows is None:
            return []
        return [
            Face(
                x=float(row[0]) / width,
                y=float(row[1]) / height,
                w=float(row[2]) / width,
                h=float(row[3]) / height,
                score=float(row[14]),
                raw=row.copy(),
            )
            for row in rows
        ]

    def fingerprint(self, image_bgr: np.ndarray, face: Face) -> np.ndarray:
        aligned = self._recognizer.alignCrop(image_bgr, face.raw)
        return self._recognizer.feature(aligned).ravel().copy()


def nearest_face(faces: list[Face]) -> Face | None:
    """The face closest to the camera, i.e. the biggest one."""
    return max(faces, key=lambda face: face.area, default=None)

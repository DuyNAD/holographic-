"""Bodies (MediaPipe Pose) link faces to hands: a hand belongs to the person
whose body has a wrist where the hand is, and a face belongs to the person whose
nose is inside it."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from holostudio import config
from holostudio.downloads import ensure_file
from holostudio.tracking.types import Hand

from .faces import Face

MAX_PEOPLE = 4
POSE_CONFIDENCE = 0.5
# How far (in frame fractions) a hand's wrist may be from a body's wrist.
HAND_TO_WRIST = 0.12
NOSE, LEFT_WRIST, RIGHT_WRIST = 0, 15, 16

Point = tuple[float, float]


@dataclass(frozen=True)
class Body:
    nose: Point
    wrists: tuple[Point, Point]  # (left, right), normalized to the frame


def ensure_pose_model() -> Path:
    return ensure_file(config.POSE_LANDMARKER_FILE, config.POSE_LANDMARKER_URL)


def face_owner(bodies: list[Body], face: Face) -> int | None:
    """The body whose nose sits inside the face box."""
    inside = [i for i, body in enumerate(bodies) if face.contains(*body.nose, margin=0.25)]
    if not inside:
        return None
    centre = face.centre
    return min(inside, key=lambda i: math.dist(bodies[i].nose, centre))


def hand_owner(bodies: list[Body], hand: Hand) -> int | None:
    """The body with a wrist closest to the hand's wrist, if close enough."""
    if not hand:
        return None
    wrist = (hand[0].x, hand[0].y)
    best, best_distance = None, HAND_TO_WRIST
    for index, body in enumerate(bodies):
        for body_wrist in body.wrists:
            distance = math.dist(wrist, body_wrist)
            if distance < best_distance:
                best, best_distance = index, distance
    return best


class PoseDetector:
    def __init__(self, model_path: Path, max_people: int = MAX_PEOPLE) -> None:
        from mediapipe.tasks.python import BaseOptions, vision

        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=max_people,
            min_pose_detection_confidence=POSE_CONFIDENCE,
            min_pose_presence_confidence=POSE_CONFIDENCE,
            min_tracking_confidence=POSE_CONFIDENCE,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def detect(self, image_bgr: np.ndarray, timestamp: float) -> list[Body]:
        import mediapipe as mp

        timestamp_ms = max(int(timestamp * 1000), self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms
        rgb = np.ascontiguousarray(image_bgr[:, :, ::-1])
        result = self._landmarker.detect_for_video(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp_ms
        )
        return [
            Body(
                nose=(pose[NOSE].x, pose[NOSE].y),
                wrists=(
                    (pose[LEFT_WRIST].x, pose[LEFT_WRIST].y),
                    (pose[RIGHT_WRIST].x, pose[RIGHT_WRIST].y),
                ),
            )
            for pose in result.pose_landmarks
        ]

    def close(self) -> None:
        self._landmarker.close()

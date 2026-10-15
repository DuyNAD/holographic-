"""MediaPipe HandLandmarker wrapper: BGR frame in, landmarks out."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from holostudio.config import MAX_TRACKED_HANDS

from .types import HandFrame, Landmark

DETECTION_CONFIDENCE = 0.55


class HandDetector:
    def __init__(self, model_path: Path, max_hands: int = MAX_TRACKED_HANDS) -> None:
        from mediapipe.tasks.python import BaseOptions, vision

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=DETECTION_CONFIDENCE,
            min_hand_presence_confidence=DETECTION_CONFIDENCE,
            min_tracking_confidence=DETECTION_CONFIDENCE,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def detect(self, image_bgr: np.ndarray, timestamp: float) -> HandFrame:
        import mediapipe as mp

        # MediaPipe VIDEO mode needs strictly increasing timestamps.
        timestamp_ms = max(int(timestamp * 1000), self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms

        rgb = np.ascontiguousarray(image_bgr[:, :, ::-1])
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(image, timestamp_ms)

        hands = tuple(
            tuple(Landmark(point.x, point.y, point.z) for point in hand)
            for hand in result.hand_landmarks
        )
        handedness = tuple(
            (categories[0].category_name if categories else "") for categories in result.handedness
        )
        world_hands = tuple(
            tuple(Landmark(point.x, point.y, point.z) for point in hand)
            for hand in result.hand_world_landmarks
        )
        height, width = image_bgr.shape[:2]
        return HandFrame(
            hands=hands,
            handedness=handedness,
            timestamp=timestamp,
            world_hands=world_hands,
            aspect=width / height,
        )

    def close(self) -> None:
        self._landmarker.close()

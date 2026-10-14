"""Prepares a camera frame for the small camera window."""

from __future__ import annotations

import cv2
import numpy as np

from holostudio.tracking.types import Hand

HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)  # fmt: skip

LINE_COLOR = (255, 231, 106)  # BGR
POINT_COLOR = (185, 255, 125)


def crop_to_aspect(image: np.ndarray, aspect: float) -> tuple[np.ndarray, tuple[float, float]]:
    """Centre-crops to the window's aspect ratio; returns the crop and its x/y offsets (0..1)."""
    height, width = image.shape[:2]
    if width / height > aspect:
        new_width = int(round(height * aspect))
        left = (width - new_width) // 2
        return image[:, left : left + new_width], (left / width, 0.0)
    new_height = int(round(width / aspect))
    top = (height - new_height) // 2
    return image[top : top + new_height, :], (0.0, top / height)


def prepare_preview(image_bgr: np.ndarray, hands: tuple[Hand, ...], aspect: float) -> np.ndarray:
    """Mirrored, cropped preview with the hand skeleton drawn on it (BGR, top row first)."""
    full_height, full_width = image_bgr.shape[:2]
    cropped, (offset_x, offset_y) = crop_to_aspect(image_bgr, aspect)
    preview = np.ascontiguousarray(cropped[:, ::-1])
    height, width = preview.shape[:2]

    def to_pixel(point) -> tuple[int, int]:
        x = (point.x - offset_x) * full_width
        y = (point.y - offset_y) * full_height
        return (int(round(width - 1 - x)), int(round(y)))

    for hand in hands:
        if len(hand) < 21:
            continue
        for start, end in HAND_CONNECTIONS:
            cv2.line(
                preview, to_pixel(hand[start]), to_pixel(hand[end]), LINE_COLOR, 2, cv2.LINE_AA
            )
        for index, point in enumerate(hand):
            cv2.circle(
                preview, to_pixel(point), 4 if index == 0 else 3, POINT_COLOR, -1, cv2.LINE_AA
            )
    return preview

"""Prepares a camera frame for the small camera window."""

from __future__ import annotations

import cv2
import numpy as np

from holostudio.tracking.types import FaceBox, Hand, Landmark

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
DESIGNER_COLOR = (125, 255, 125)  # BGR green
CANDIDATE_COLOR = (60, 220, 255)  # BGR amber: recorded, waiting for confirmation
OTHER_FACE_COLOR = (140, 140, 140)


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


def prepare_preview(
    image_bgr: np.ndarray,
    hands: tuple[Hand, ...],
    aspect: float,
    designer_face: FaceBox | None = None,
    other_faces: tuple[FaceBox, ...] = (),
    candidate: bool = False,
) -> np.ndarray:
    """Mirrored, cropped preview with the hand skeleton drawn on it (BGR, top row first)."""
    full_height, full_width = image_bgr.shape[:2]
    cropped, (offset_x, offset_y) = crop_to_aspect(image_bgr, aspect)
    preview = np.ascontiguousarray(cropped[:, ::-1])
    height, width = preview.shape[:2]

    def to_pixel(point) -> tuple[int, int]:
        x = (point.x - offset_x) * full_width
        y = (point.y - offset_y) * full_height
        return (int(round(width - 1 - x)), int(round(y)))

    def face_rect(face: FaceBox) -> tuple[tuple[int, int], tuple[int, int]]:
        # Mirrored: the face's right edge in the camera image is on the left on screen.
        top_left = to_pixel(Landmark(face.x + face.w, face.y, 0))
        bottom_right = to_pixel(Landmark(face.x, face.y + face.h, 0))
        return top_left, bottom_right

    for face in other_faces:
        cv2.rectangle(preview, *face_rect(face), OTHER_FACE_COLOR, 1, cv2.LINE_AA)
    if designer_face is not None:
        color = CANDIDATE_COLOR if candidate else DESIGNER_COLOR
        cv2.rectangle(preview, *face_rect(designer_face), color, 2, cv2.LINE_AA)

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

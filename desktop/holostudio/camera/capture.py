"""Webcam capture on a background thread; the newest frame is always available."""

from __future__ import annotations

import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np

from holostudio import config

CameraStatus = Literal[
    "idle", "requesting", "active", "blocked", "unavailable", "disconnected", "error"
]

STATUS_LABELS: dict[CameraStatus, str] = {
    "idle": "Đang tắt",
    "requesting": "Đang kết nối",
    "active": "Đang hoạt động",
    "blocked": "Hình bị đen",
    "unavailable": "Không khả dụng",
    "disconnected": "Mất kết nối",
    "error": "Có lỗi",
}

STATUS_MESSAGES: dict[CameraStatus, str] = {
    "idle": "Camera đang tắt.",
    "requesting": "Đang kết nối camera…",
    "active": "Camera đang hoạt động trên thiết bị.",
    "blocked": (
        "Camera chỉ trả về hình đen. Hãy đóng ứng dụng khác đang dùng camera "
        "(trình duyệt, Teams, Zoom, cửa sổ Holographic Studio khác) hoặc mở nắp che ống kính."
    ),
    "unavailable": (
        "Không mở được camera. Hãy kiểm tra webcam, quyền camera của Windows "
        "hoặc ứng dụng khác đang dùng camera."
    ),
    "disconnected": "Camera đã bị ngắt kết nối. Hãy cắm lại rồi bật camera.",
    "error": "Không thể khởi động camera. Vui lòng thử lại.",
}

# Consecutive failed reads before the camera counts as unplugged.
MAX_FAILED_READS = 30
# A camera held by another app (or covered) keeps sending pure black frames.
BLACK_LEVEL = 3.0
BLACK_SECONDS = 2.0


def is_black(image: np.ndarray) -> bool:
    # Sample a sparse grid so the check stays cheap on every frame.
    return float(image[::16, ::16].mean()) < BLACK_LEVEL


class VideoSource(Protocol):
    def isOpened(self) -> bool: ...  # noqa: N802 - OpenCV naming
    def read(self) -> tuple[bool, np.ndarray | None]: ...
    def release(self) -> None: ...


def open_webcam(index: int) -> VideoSource:
    import cv2

    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    capture = cv2.VideoCapture(index, backend)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    capture.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
    return capture


@dataclass(frozen=True)
class Frame:
    image: np.ndarray  # BGR, as delivered by the camera
    timestamp: float  # seconds, monotonic
    index: int


class CameraStream:
    def __init__(
        self,
        index: int = config.CAMERA_INDEX,
        opener: Callable[[int], VideoSource] = open_webcam,
    ) -> None:
        self._index = index
        self._opener = opener
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._frame: Frame | None = None
        self._status: CameraStatus = "idle"

    @property
    def status(self) -> CameraStatus:
        return self._status

    @property
    def message(self) -> str:
        return STATUS_MESSAGES[self._status]

    @property
    def active(self) -> bool:
        return self._status == "active"

    def latest_frame(self) -> Frame | None:
        with self._lock:
            return self._frame

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._status = "requesting"
        self._thread = threading.Thread(target=self._run, name="camera", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        self._thread = None
        with self._lock:
            self._frame = None
        self._status = "idle"

    def wait_until_settled(self, timeout: float = 5) -> CameraStatus:
        """Blocks until the camera leaves the 'requesting' state (used by tests and tools)."""
        deadline = time.monotonic() + timeout
        while self._status == "requesting" and time.monotonic() < deadline:
            time.sleep(0.01)
        return self._status

    def _run(self) -> None:
        try:
            source = self._opener(self._index)
        except Exception:
            self._status = "error"
            return

        try:
            if not source.isOpened():
                self._status = "unavailable"
                return

            failed_reads = 0
            frame_index = 0
            black_since: float | None = None
            while not self._stop.is_set():
                ok, image = source.read()
                if not ok or image is None:
                    failed_reads += 1
                    if failed_reads >= MAX_FAILED_READS:
                        self._status = "disconnected"
                        with self._lock:
                            self._frame = None
                        return
                    time.sleep(0.01)
                    continue

                failed_reads = 0
                frame_index += 1
                now = time.monotonic()
                with self._lock:
                    self._frame = Frame(image, now, frame_index)
                if not is_black(image):
                    black_since = None
                    self._status = "active"
                elif black_since is None:
                    black_since = now
                elif now - black_since >= BLACK_SECONDS:
                    self._status = "blocked"
        finally:
            source.release()

"""Runs hand detection on its own thread so rendering never waits for MediaPipe."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol

from holostudio.camera.capture import CameraStream, Frame
from holostudio.config import MAX_TRACKED_HANDS

from .types import HandFrame, TrackingState


class Detector(Protocol):
    def detect(self, image, timestamp: float) -> HandFrame: ...
    def close(self) -> None: ...


def _default_detector() -> Detector:
    from .detector import HandDetector
    from .model import ensure_hand_model

    return HandDetector(ensure_hand_model())


IDLE = TrackingState()
NO_HAND_MESSAGE = "Đưa bàn tay vào giữa khung hình."


class TrackingWorker:
    def __init__(
        self,
        camera: CameraStream,
        detector_factory: Callable[[], Detector] = _default_detector,
    ) -> None:
        self._camera = camera
        self._factory = detector_factory
        self._lock = threading.Lock()
        self._state = IDLE
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def state(self) -> TrackingState:
        with self._lock:
            return self._state

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="tracking", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._thread = None
        self._set(IDLE)

    def _set(self, state: TrackingState) -> None:
        with self._lock:
            self._state = state

    def _run(self) -> None:
        self._set(TrackingState("loading", "Đang tải mô hình nhận diện tay…"))
        try:
            detector = self._factory()
        except Exception:
            self._set(TrackingState("error", "Không thể tải mô hình nhận diện tay."))
            return

        last_index = -1
        try:
            while not self._stop.is_set():
                frame: Frame | None = self._camera.latest_frame()
                if frame is None or frame.index == last_index:
                    if not self._camera.active and self.state.status != "loading":
                        self._set(TrackingState("idle", IDLE.message))
                    time.sleep(0.003)
                    continue
                last_index = frame.index

                try:
                    hand_frame = detector.detect(frame.image, frame.timestamp)
                except Exception:
                    # One bad frame must not stop tracking: report it and keep going.
                    self._set(TrackingState("error", "Không thể xử lý khung hình camera."))
                    continue

                count = len(hand_frame.hands)
                self._set(
                    TrackingState(
                        "tracking" if count else "no-hand",
                        f"Đã nhận diện {count}/{MAX_TRACKED_HANDS} bàn tay."
                        if count
                        else NO_HAND_MESSAGE,
                        hand_frame,
                    )
                )
        finally:
            detector.close()

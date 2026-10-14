import time

import numpy as np
import pytest

from holostudio.camera.capture import Frame
from holostudio.config import HAND_LANDMARKER_FILE
from holostudio.tracking.types import HandFrame, Landmark
from holostudio.tracking.worker import TrackingWorker


class FakeCamera:
    def __init__(self):
        self.frame = None
        self.active = True

    def latest_frame(self):
        return self.frame


HAND = tuple(Landmark(0.5, 0.5, 0) for _ in range(21))


class FakeDetector:
    def __init__(self, fail_on=()):
        self.fail_on = set(fail_on)
        self.closed = False

    def detect(self, image, timestamp):
        if int(image[0, 0, 0]) in self.fail_on:
            raise RuntimeError("bad frame")
        hands = (HAND,) if image[0, 0, 0] % 2 else ()
        return HandFrame(hands, ("Right",) * len(hands), timestamp)

    def close(self):
        self.closed = True


def wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


def push(camera, value, index):
    camera.frame = Frame(np.full((4, 4, 3), value, dtype=np.uint8), time.monotonic(), index)


def test_publishes_tracking_and_no_hand_states():
    camera = FakeCamera()
    worker = TrackingWorker(camera, FakeDetector)
    worker.start()
    try:
        push(camera, 1, 1)
        assert wait_for(lambda: worker.state.status == "tracking")
        assert worker.state.message == "Đã nhận diện 1/2 bàn tay."
        assert worker.state.frame.hands == (HAND,)

        push(camera, 2, 2)
        assert wait_for(lambda: worker.state.status == "no-hand")
    finally:
        worker.stop()
    assert worker.state.status == "idle"


def test_keeps_running_after_a_bad_frame():
    camera = FakeCamera()
    worker = TrackingWorker(camera, lambda: FakeDetector(fail_on={3}))
    worker.start()
    try:
        push(camera, 3, 1)
        assert wait_for(lambda: worker.state.status == "error")
        push(camera, 5, 2)
        assert wait_for(lambda: worker.state.status == "tracking")
    finally:
        worker.stop()


def test_reports_a_model_that_cannot_load():
    def broken():
        raise RuntimeError("no model")

    worker = TrackingWorker(FakeCamera(), broken)
    worker.start()
    try:
        assert wait_for(lambda: worker.state.status == "error")
        assert worker.state.message == "Không thể tải mô hình nhận diện tay."
    finally:
        worker.stop()


@pytest.mark.skipif(not HAND_LANDMARKER_FILE.exists(), reason="hand model not downloaded")
def test_real_mediapipe_detector_runs_fast_on_a_camera_sized_frame():
    from holostudio.tracking.detector import HandDetector

    detector = HandDetector(HAND_LANDMARKER_FILE)
    try:
        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        detector.detect(frame, 0.0)  # warm-up
        started = time.perf_counter()
        for index in range(1, 11):
            result = detector.detect(frame, index / 30)
        per_frame = (time.perf_counter() - started) / 10
    finally:
        detector.close()

    assert result.hands == ()
    assert per_frame < 0.1, f"{per_frame * 1000:.1f} ms per frame"

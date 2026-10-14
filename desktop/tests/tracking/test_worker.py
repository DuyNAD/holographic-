import time

import numpy as np
import pytest

from holostudio.camera.capture import Frame
from holostudio.config import HAND_LANDMARKER_FILE
from holostudio.tracking.types import HandFrame, Landmark, TrackingState
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


class FakeIdentity:
    """Every hand is the designer's once enrolment was requested."""

    def __init__(self):
        self.enrolled = False

    def request_enrollment(self, now):
        self.enrolled = True

    def confirm(self):
        self.confirmed = True

    def cancel(self):
        self.enrolled = False

    def process(self, image, timestamp, hands):
        from holostudio.tracking.types import DesignerInfo

        if not self.enrolled:
            return tuple(False for _ in hands), DesignerInfo()
        return tuple(True for _ in hands), DesignerInfo("locked", "Đã khóa người thiết kế")

    def close(self):
        pass


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
    worker = TrackingWorker(camera, FakeDetector, FakeIdentity)
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
    worker = TrackingWorker(camera, lambda: FakeDetector(fail_on={3}), FakeIdentity)
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

    worker = TrackingWorker(FakeCamera(), broken, FakeIdentity)
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


def test_choosing_a_designer_marks_their_hands():
    camera = FakeCamera()
    worker = TrackingWorker(camera, FakeDetector, FakeIdentity)
    worker.start()
    try:
        push(camera, 1, 1)
        assert wait_for(lambda: worker.state.status == "tracking")
        assert worker.state.designer.status == "unset"
        assert worker.state.frame.designer_hands == (False,)

        worker.request_designer()
        push(camera, 1, 2)
        assert wait_for(lambda: worker.state.designer.locked)
        assert worker.state.frame.designer_hands == (True,)
    finally:
        worker.stop()


def test_hand_tracking_keeps_working_if_the_identity_models_fail():
    def broken_identity():
        raise RuntimeError("no face model")

    camera = FakeCamera()
    worker = TrackingWorker(camera, FakeDetector, broken_identity)
    worker.start()
    try:
        push(camera, 1, 1)
        assert wait_for(lambda: worker.state.status == "tracking")
        assert worker.state.designer.status == "unavailable"
        assert worker.state.frame.designer_hands == (False,)
    finally:
        worker.stop()


def test_designer_only_keeps_just_the_designers_hands():
    from holostudio.tracking.types import DesignerInfo

    other = tuple(Landmark(0.9, 0.9, 0) for _ in range(21))
    state = TrackingState(
        "tracking",
        "",
        HandFrame((HAND, other), ("Right", "Left"), 1.0, (True, False)),
        DesignerInfo("locked", ""),
    )
    mine = state.designer_only()
    assert mine.frame.hands == (HAND,)
    assert mine.frame.handedness == ("Right",)
    assert mine.status == "tracking"

    nobody = TrackingState("tracking", "", HandFrame((other,), ("Left",), 1.0, (False,)))
    assert nobody.designer_only().status == "no-hand"


def test_confirm_and_cancel_reach_the_identity_thread():
    camera = FakeCamera()
    identities = []

    def factory():
        identities.append(FakeIdentity())
        return identities[-1]

    worker = TrackingWorker(camera, FakeDetector, factory)
    worker.confirm_designer()  # before tracking starts: ignored safely
    worker.start()
    try:
        push(camera, 1, 1)
        assert wait_for(lambda: worker.state.status == "tracking")
        worker.request_designer()
        push(camera, 1, 2)
        assert wait_for(lambda: identities[0].enrolled)
        worker.confirm_designer()
        assert getattr(identities[0], "confirmed", False)
        worker.cancel_designer()
        assert not identities[0].enrolled
    finally:
        worker.stop()

import time

import numpy as np
import pytest

from holostudio import config
from holostudio.identity.bodies import Body
from holostudio.identity.faces import Face
from holostudio.identity.pipeline import IdentityPipeline
from holostudio.tracking.types import Landmark

ASSETS = config.DATA_DIR / "test-assets"
FINGERPRINT = np.ones(128)


class FakeFaces:
    def detect(self, image):
        return [Face(0.4, 0.2, 0.2, 0.26, 0.9, np.zeros(15, np.float32))]

    def fingerprint(self, image, face):
        return FINGERPRINT


class SlowPoses:
    """Pose detection that takes a while, like the real model."""

    def detect(self, image, timestamp):
        time.sleep(0.03)
        return [Body(nose=(0.5, 0.35), wrists=((0.4, 0.7), (0.6, 0.7)))]

    def close(self):
        pass


def designer_hand():
    return tuple(Landmark(0.6, 0.7, 0) for _ in range(21))


def stranger_hand():
    return tuple(Landmark(0.05, 0.2, 0) for _ in range(21))


def wait_for(predicate, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


def test_hands_are_answered_at_once_while_identity_runs_on_its_own_thread():
    pipeline = IdentityPipeline(FakeFaces(), SlowPoses())
    image = np.zeros((36, 64, 3), np.uint8)
    try:
        started = time.perf_counter()
        mask, info = pipeline.process(image, 0.0, (designer_hand(),))
        assert time.perf_counter() - started < 0.01  # never waits for pose detection
        assert mask == (False,) and info.status == "unset"

        pipeline.request_enrollment(0.0)
        t = 0.0

        def locked():
            nonlocal t
            t += 1 / 30
            pipeline.process(image, t, ())
            return pipeline.process(image, t, ())[1].status == "locked"

        def status():
            nonlocal t
            t += 1 / 30
            pipeline.process(image, t, ())
            return pipeline.process(image, t, ())[1].status

        assert wait_for(lambda: status() == "pending")
        # While waiting for confirmation, the candidate's hands are already known.
        mask, info = pipeline.process(image, t, (designer_hand(), stranger_hand()))
        assert mask == (True, False) and info.pending

        pipeline.confirm()
        assert wait_for(locked)
        mask, info = pipeline.process(image, t, (designer_hand(), stranger_hand()))
        assert mask == (True, False)
        assert info.face is not None
    finally:
        pipeline.close()


needs_models = pytest.mark.skipif(
    not (
        config.POSE_LANDMARKER_FILE.exists()
        and config.FACE_DETECTOR_FILE.exists()
        and config.FACE_RECOGNIZER_FILE.exists()
        and (ASSETS / "messi5.jpg").exists()
    ),
    reason="identity models or test image not downloaded",
)


@needs_models
def test_real_models_lock_the_person_in_the_photo():
    import cv2

    from holostudio.identity.pipeline import default_identity_pipeline

    photo = cv2.resize(cv2.imread(str(ASSETS / "messi5.jpg")), (640, 360))
    pipeline = default_identity_pipeline()
    try:
        pipeline.request_enrollment(0.0)
        t = 0.0

        def locked():
            nonlocal t
            t += 1 / 30
            time.sleep(1 / 30)
            return pipeline.process(photo, t, ())[1].status == "locked"

        def pending():
            nonlocal t
            t += 1 / 30
            time.sleep(1 / 30)
            return pipeline.process(photo, t, ())[1].status == "pending"

        assert wait_for(pending, timeout=10)
        pipeline.confirm()
        assert wait_for(locked, timeout=5)
        face = pipeline.process(photo, t, ())[1].face
        assert face is not None and 0.3 < face.x < 0.5
    finally:
        pipeline.close()

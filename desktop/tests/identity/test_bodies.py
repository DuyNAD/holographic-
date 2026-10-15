import pytest

from holostudio import config
from holostudio.identity.bodies import Body, PoseDetector, hand_owner
from holostudio.tracking.types import Landmark

ASSETS = config.DATA_DIR / "test-assets"


def hand_at(x, y):
    return tuple(Landmark(x, y, 0) for _ in range(21))


ALICE = Body(nose=(0.3, 0.3), wrists=((0.2, 0.7), (0.4, 0.7)))
BOB = Body(nose=(0.75, 0.35), wrists=((0.65, 0.75), (0.85, 0.75)))


def test_a_hand_belongs_to_the_body_with_a_wrist_next_to_it():
    assert hand_owner([ALICE, BOB], hand_at(0.41, 0.69)) == 0
    assert hand_owner([ALICE, BOB], hand_at(0.66, 0.76)) == 1
    assert hand_owner([ALICE, BOB], hand_at(0.5, 0.1)) is None  # nobody's wrist is there
    assert hand_owner([], hand_at(0.4, 0.7)) is None


needs_models = pytest.mark.skipif(
    not (config.POSE_LANDMARKER_FILE.exists() and (ASSETS / "messi5.jpg").exists()),
    reason="pose model or test image not downloaded",
)


@needs_models
def test_pose_runs_fast_enough_for_live_video():
    import time

    import cv2

    frame = cv2.resize(cv2.imread(str(ASSETS / "messi5.jpg")), (640, 360))
    detector = PoseDetector(config.POSE_LANDMARKER_FILE)
    try:
        detector.detect(frame, 0.0)
        timings = []
        for index in range(1, 16):
            started = time.perf_counter()
            detector.detect(frame, index / 30)
            timings.append(time.perf_counter() - started)
    finally:
        detector.close()
    # The median ignores a slow frame caused by other programs on the machine.
    per_frame = sorted(timings)[len(timings) // 2]
    assert per_frame < 0.05, f"{per_frame * 1000:.1f} ms"

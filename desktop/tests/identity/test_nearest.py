import time

import numpy as np
import pytest

from holostudio import config
from holostudio.identity.bodies import Body
from holostudio.identity.nearest import (
    SWITCH_SECONDS,
    NearestUser,
    NearestUserFilter,
    nearest_hand_mask,
    palm_size,
)
from holostudio.tracking.types import Landmark

ASSETS = config.DATA_DIR / "test-assets"


def person(x, shoulder_width):
    """A body centred at x; wider shoulders = closer to the camera."""
    half = shoulder_width / 2
    return Body(
        nose=(x, 0.3),
        wrists=((x - 0.12, 0.7), (x + 0.12, 0.7)),
        shoulders=((x - half, 0.45), (x + half, 0.45)),
    )


def hand_at(x, y=0.7, palm=0.08):
    points = [Landmark(x, y - palm / 2, 0)] * 21
    points[0] = Landmark(x, y, 0)
    points[9] = Landmark(x, y - palm, 0)
    return tuple(points)


def test_the_person_with_the_widest_shoulders_is_the_user():
    nearest = NearestUser()
    assert nearest.update([person(0.25, 0.15), person(0.7, 0.3)], 0.0) == 1
    assert nearest.update([], 0.1) is None


def test_control_does_not_flicker_between_people_at_about_the_same_distance():
    nearest = NearestUser()
    near, other = person(0.3, 0.30), person(0.7, 0.32)  # other is only ~7% bigger
    t = 0.0
    assert nearest.update([near, person(0.7, 0.2)], t) == 0
    for _ in range(60):
        t += 1 / 30
        assert nearest.update([near, other], t) == 0


def test_control_moves_to_someone_who_comes_clearly_closer():
    nearest = NearestUser()
    t = 0.0
    nearest.update([person(0.3, 0.3), person(0.7, 0.2)], t)
    closer = person(0.7, 0.45)  # 50% bigger than the current user
    chosen = []
    for _ in range(int(SWITCH_SECONDS * 30) + 5):
        t += 1 / 30
        chosen.append(nearest.update([person(0.3, 0.3), closer], t))
    assert chosen[0] == 0  # not straight away…
    assert chosen[-1] == 1  # …but after the switch delay


def test_the_user_is_followed_when_the_list_order_changes():
    nearest = NearestUser()
    user, other = person(0.3, 0.3), person(0.7, 0.2)
    nearest.update([user, other], 0.0)
    assert nearest.update([other, user], 1 / 30) == 1


def test_only_the_nearest_users_hands_are_kept():
    bodies = [person(0.3, 0.3), person(0.7, 0.2)]
    user_hand, other_hand = hand_at(0.42), hand_at(0.82, palm=0.05)
    assert nearest_hand_mask(bodies, 0, (user_hand, other_hand)) == (True, False)


def test_without_a_matching_body_only_the_biggest_hands_are_kept():
    near, far = hand_at(0.3, palm=0.12), hand_at(0.7, palm=0.05)
    assert nearest_hand_mask([], None, (near, far)) == (True, False)
    # Two hands of one person sitting very close: both are about as big.
    assert nearest_hand_mask([], None, (near, hand_at(0.6, palm=0.11))) == (True, True)
    assert palm_size(near) == pytest.approx(0.12)


class SlowPoses:
    def __init__(self, bodies):
        self.bodies = bodies

    def detect(self, image, timestamp):
        time.sleep(0.03)
        return self.bodies

    def close(self):
        pass


def test_the_filter_answers_at_once_while_pose_runs_on_its_own_thread():
    poses = SlowPoses([person(0.3, 0.3), person(0.7, 0.2)])
    hands = (hand_at(0.42), hand_at(0.82, palm=0.05))
    image = np.zeros((36, 64, 3), np.uint8)
    pose_filter = NearestUserFilter(poses)
    try:
        started = time.perf_counter()
        pose_filter.mask(image, 0.0, hands)
        assert time.perf_counter() - started < 0.01  # never waits for pose detection

        deadline, t = time.monotonic() + 3, 0.0
        while time.monotonic() < deadline:
            t += 1 / 30
            if pose_filter.mask(image, t, hands) == (True, False):
                break
            time.sleep(0.01)
        assert pose_filter.mask(image, t, hands) == (True, False)
    finally:
        pose_filter.close()


@pytest.mark.skipif(
    not (config.POSE_LANDMARKER_FILE.exists() and (ASSETS / "messi5.jpg").exists()),
    reason="pose model or test image not downloaded",
)
def test_real_pose_finds_the_person_and_keeps_a_hand_at_their_wrist():
    import cv2

    from holostudio.identity.nearest import default_nearest_filter

    photo = cv2.resize(cv2.imread(str(ASSETS / "messi5.jpg")), (640, 360))
    pose_filter = default_nearest_filter()
    try:
        deadline, t = time.monotonic() + 10, 0.0
        latest = None
        while time.monotonic() < deadline:
            t += 1 / 30
            pose_filter.mask(photo, t, ())
            latest = pose_filter._latest
            if latest.bodies:
                break
            time.sleep(1 / 30)
        assert latest is not None and latest.nearest is not None
        wrist = latest.bodies[latest.nearest].wrists[0]
        at_wrist = hand_at(wrist[0], wrist[1])
        far_away = hand_at(0.02, 0.02, palm=0.02)
        assert pose_filter.mask(photo, t, (at_wrist, far_away)) == (True, False)
    finally:
        pose_filter.close()

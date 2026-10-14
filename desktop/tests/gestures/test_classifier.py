import random
import statistics

import pytest

from holostudio.gestures.classifier import Observation, detect_gesture
from holostudio.gestures.filters import OneEuroHandFilter
from holostudio.tracking.types import Landmark

from .helpers import make_curved_pinch, make_hand, make_real_fist


@pytest.mark.parametrize(
    ("extended", "expected"),
    [((0, 1, 2, 3), "open-palm"), ((0,), "point"), ((), "fist")],
)
def test_detects_basic_gestures(extended, expected):
    assert detect_gesture(make_hand(extended)).name == expected


def test_pinch_has_priority_when_thumb_and_index_touch():
    assert detect_gesture(make_hand((0,), pinch=True)).name == "pinch"


def test_rejects_incomplete_landmarks():
    assert detect_gesture(()) == Observation("none", 0.0)


def half_open_pinch():
    """Thumb and index 0.42 palm-lengths apart: between entering and releasing a pinch."""
    hand = list(make_hand((0,)))
    palm = abs(hand[0].y - hand[9].y)
    hand[4] = Landmark(hand[8].x - 0.42 * palm, hand[8].y, 0)
    return tuple(hand)


def test_a_pinch_is_held_until_the_fingers_clearly_open():
    hand = half_open_pinch()
    assert detect_gesture(hand).name != "pinch"  # too open to start a pinch
    held = detect_gesture(hand, current="pinch")
    assert held.name == "pinch" and held.confidence >= 0.6  # but not open enough to release


def test_one_euro_filter_removes_jitter_from_a_still_hand():
    random.seed(3)
    filt = OneEuroHandFilter()
    still = Landmark(0.5, 0.5, 0)
    raw, filtered = [], []
    for frame in range(90):
        noisy = Landmark(still.x + random.gauss(0, 0.004), still.y, 0)
        raw.append(noisy.x)
        filtered.append(filt((noisy,), frame / 30)[0].x)

    assert statistics.pstdev(filtered[30:]) < statistics.pstdev(raw[30:]) * 0.4


def test_one_euro_filter_follows_a_fast_move_quickly():
    filt = OneEuroHandFilter()
    filt((Landmark(0.2, 0.5, 0),), 0.0)
    for frame in range(1, 6):  # ~170 ms after jumping across the screen
        x = filt((Landmark(0.8, 0.5, 0),), frame / 30)[0].x
    assert x > 0.2 + 0.9 * 0.6


def test_a_real_fist_is_not_mistaken_for_a_pinch():
    # The thumb lies across the index finger, so thumb tip and index tip are close.
    assert detect_gesture(make_real_fist()).name == "fist"


def test_a_fist_with_a_loose_pinky_is_still_a_fist():
    assert detect_gesture(make_real_fist(loose_pinky=True)).name == "fist"


def test_a_curved_ok_pinch_is_still_a_pinch():
    assert detect_gesture(make_curved_pinch()).name == "pinch"


def test_a_held_fist_tolerates_one_more_loose_finger():
    hand = list(make_real_fist(loose_pinky=True))
    hand[16] = Landmark(hand[16].x, 0.4, 0)  # ring finger loosens too while moving
    hand = tuple(hand)
    assert detect_gesture(hand).name != "fist"
    assert detect_gesture(hand, current="fist").name == "fist"

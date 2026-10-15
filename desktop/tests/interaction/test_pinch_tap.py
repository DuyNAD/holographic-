from holostudio.gestures.engine import StableGesture
from holostudio.interaction.pinch_tap import PinchTaps
from holostudio.tracking.types import Landmark


def gesture(name, track_id, x=0.4, y=0.5):
    landmarks = [Landmark(0.5, 0.5, 0)] * 21
    landmarks[8] = Landmark(1 - x, y, 0)
    return StableGesture(0, "Right", name, 1.0, tuple(landmarks), track_id)


def test_each_new_pinch_counts_once():
    taps = PinchTaps()
    assert taps.update((gesture("point", 1),)) == []
    assert taps.update((gesture("pinch", 1),)) == [(0.4, 0.5)]
    assert taps.update((gesture("pinch", 1),)) == []  # still holding: no second tap
    taps.update((gesture("point", 1),))
    assert len(taps.update((gesture("pinch", 1),))) == 1  # pinch again: a new tap


def test_two_hands_tap_independently():
    taps = PinchTaps()
    taps.update((gesture("pinch", 1),))
    assert taps.update((gesture("pinch", 1), gesture("pinch", 2, x=0.7))) == [(0.7, 0.5)]

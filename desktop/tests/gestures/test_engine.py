from dataclasses import replace

import pytest

from holostudio.gestures.classifier import Observation
from holostudio.gestures.engine import GestureEngine
from holostudio.gestures.state_machine import GestureMachine, advance
from holostudio.tracking.types import HandFrame, TrackingState

from .helpers import make_hand


def tracking(hands, handedness, timestamp):
    return TrackingState("tracking", "", HandFrame(tuple(hands), tuple(handedness), timestamp))


def test_requires_consecutive_confident_frames_before_activation():
    first = advance(GestureMachine(), Observation("pinch", 1))
    second = advance(first, Observation("pinch", 1))
    assert first.current == "none"
    assert second.current == "pinch"


def test_ignores_one_jitter_frame_and_releases_after_two():
    active = replace(GestureMachine(), current="pinch", confidence=0.9)
    once = advance(active, Observation("none", 0))
    assert once.current == "pinch"
    assert once.missing_frames == 1
    assert advance(once, Observation("none", 0)).current == "none"


def test_low_confidence_does_not_activate():
    machine = advance(GestureMachine(), Observation("pinch", 0.3))
    assert advance(machine, Observation("pinch", 0.3)).current == "none"


def test_engine_reports_stable_gestures_per_hand():
    engine = GestureEngine()
    hands = [make_hand((0,)), make_hand((), offset_x=0.2)]

    engine.update(tracking(hands, ["Left", "Right"], 1))
    gestures = engine.update(tracking(hands, ["Left", "Right"], 2))

    assert [(g.handedness, g.name) for g in gestures] == [("Left", "point"), ("Right", "fist")]


def test_engine_keeps_each_hand_separate_when_mediapipe_swaps_order():
    engine = GestureEngine()
    point, fist = make_hand((0,)), make_hand((), offset_x=0.3)

    engine.update(tracking([point, fist], ["Left", "Right"], 1))
    gestures = engine.update(tracking([fist, point], ["Right", "Left"], 2))

    by_hand = {g.handedness: g for g in gestures}
    assert by_hand["Left"].name == "point"
    assert by_hand["Right"].name == "fist"
    # Filtering must not blend the two hands together after the swap.
    assert by_hand["Left"].landmarks[0].x == pytest.approx(point[0].x)
    assert by_hand["Right"].landmarks[0].x == pytest.approx(fist[0].x)


def test_engine_ignores_repeated_frames_and_resets_when_tracking_stops():
    engine = GestureEngine()
    frame = tracking([make_hand((0,))], ["Left"], 1)

    engine.update(frame)
    assert engine.update(frame) == ()  # same frame again must not advance the debounce
    assert len(engine.update(tracking([make_hand((0,))], ["Left"], 2))) == 1
    assert engine.update(TrackingState("no-hand")) == ()


def test_a_steady_hand_stays_recognised_when_mediapipe_flips_its_label():
    import random

    from holostudio.tracking.types import Landmark

    random.seed(1)
    engine = GestureEngine()
    hand = make_hand((0,))
    recognised = 0
    for frame in range(1, 301):
        noisy = tuple(
            Landmark(p.x + random.gauss(0, 0.003), p.y + random.gauss(0, 0.003), p.z) for p in hand
        )
        label = random.choice(["Left", "Right"])
        gestures = engine.update(tracking([noisy], [label], frame / 30))
        recognised += bool(gestures and gestures[0].name == "point")
    assert recognised >= 295


def test_two_hands_are_followed_by_position():
    engine = GestureEngine()
    left, right = make_hand((0,)), make_hand((), offset_x=0.3)
    engine.update(tracking([left, right], ["Right", "Right"], 1))
    gestures = engine.update(tracking([right, left], ["Left", "Left"], 2))
    by_x = sorted(gestures, key=lambda g: g.landmarks[0].x)
    assert [g.name for g in by_x] == ["point", "fist"]

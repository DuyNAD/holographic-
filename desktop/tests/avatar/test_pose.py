import math

import numpy as np
import pytest

from holostudio.avatar.pose import ViewRig, retarget, solve, units_per_metre
from holostudio.avatar.profile import HandProfile, bone_lengths
from holostudio.gestures.engine import TrackedHand
from holostudio.interaction.coordinates import landmark_to_screen
from holostudio.tracking.types import Landmark

from .test_depth import ASPECT, WORLD, project

TAN = math.tan(math.radians(21))
FORWARD = np.array([0.0, 0.0, -1.0])
RIGHT = np.array([1.0, 0.0, 0.0])
UP = np.array([0.0, 1.0, 0.0])
ORIGIN = np.array([0.0, 0.0, 10.0])


def pinhole_ray(point):
    x, y = point[0] * 2 - 1, 1 - point[1] * 2
    direction = FORWARD + x * TAN * ASPECT * RIGHT + y * TAN * UP
    return direction / np.linalg.norm(direction)


def to_screen(p):
    rel = p - ORIGIN
    depth = rel @ FORWARD
    return (0.5 + rel @ RIGHT / (depth * TAN * ASPECT) / 2, 0.5 - rel @ UP / (depth * TAN) / 2)


RIG = ViewRig(ORIGIN, RIGHT, UP, FORWARD, pinhole_ray, TAN, reach=10.0)
PROFILE = HandProfile(bone_lengths(WORLD), reference_scale=3.0)


def hand(centre=(0.45, 0.55), scale=3.0, world=WORLD):
    return TrackedHand(7, project(world, centre, scale), world, "point", ASPECT)


def test_the_virtual_hand_covers_the_screen_where_the_real_hand_is_in_the_mirror():
    virtual = solve(hand(), PROFILE, RIG)
    for joint, landmark in zip(virtual.joints, hand().landmarks, strict=True):
        assert to_screen(joint) == pytest.approx(landmark_to_screen(landmark), abs=1e-6)
    assert virtual.track_id == 7 and virtual.gesture == "point"


def test_at_the_scanned_distance_the_hand_is_as_deep_as_the_scene_centre():
    virtual = solve(hand(), PROFILE, RIG)
    assert virtual.distance == pytest.approx(1.0)
    assert np.mean(virtual.joints[[0, 5, 9, 13, 17]], axis=0)[2] == pytest.approx(0.0)


def test_twice_as_close_sits_half_as_deep_and_keeps_its_real_size():
    near = solve(hand(scale=6.0), PROFILE, RIG)
    far = solve(hand(scale=3.0), PROFILE, RIG)
    assert near.distance == pytest.approx(0.5)
    depth = ORIGIN[2] - np.mean(near.joints[[0, 5, 9, 13, 17]], axis=0)[2]
    assert depth == pytest.approx(5.0)
    span = np.linalg.norm(near.joints[12] - near.joints[0])
    assert span == pytest.approx(np.linalg.norm(far.joints[12] - far.joints[0]))


def test_bones_take_the_scanned_lengths():
    longer = HandProfile(tuple(length * 1.2 for length in PROFILE.bones), 3.0)
    virtual = solve(hand(), longer, RIG)
    k = units_per_metre(longer, RIG)
    assert virtual.units_per_metre == pytest.approx(k)
    assert np.linalg.norm(virtual.joints[8] - virtual.joints[7]) == pytest.approx(
        longer.bones[7] * k
    )


def test_a_fingertip_pointing_at_the_webcam_points_at_the_viewer():
    world = list(WORLD)
    world[8] = Landmark(world[7].x, world[7].y, world[7].z - 0.02)  # toward the webcam
    virtual = solve(hand(world=tuple(world)), PROFILE, RIG)
    assert virtual.joints[8][2] > virtual.joints[7][2]  # scene z points at the viewer


def test_retarget_keeps_directions_and_unmeasurable_hands_are_skipped():
    joints = retarget(WORLD, tuple(2 * length for length in PROFILE.bones))
    assert np.linalg.norm(joints[5] - joints[0]) == pytest.approx(2 * PROFILE.bones[4])
    flat = TrackedHand(1, tuple(Landmark(0.5, 0.5, 0) for _ in range(21)), WORLD, "none", ASPECT)
    assert solve(flat, PROFILE, RIG) is None
    assert solve(TrackedHand(1, hand().landmarks, (), "none", ASPECT), PROFILE, RIG) is None


def test_distance_is_clamped():
    assert solve(hand(scale=100.0), PROFILE, RIG).distance == pytest.approx(0.4)

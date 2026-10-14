import math
import random

import numpy as np
import pytest

from holostudio.scene.rotation import (
    axis_angle_matrix,
    euler_xyz_from_matrix,
    euler_xyz_matrix,
    turn_in_world,
)


def test_euler_angles_round_trip_through_the_matrix():
    random.seed(5)
    for _ in range(200):
        rotation = (random.uniform(-3, 3), random.uniform(-1.5, 1.5), random.uniform(-3, 3))
        back = euler_xyz_from_matrix(euler_xyz_matrix(rotation))
        assert euler_xyz_matrix(back) == pytest.approx(euler_xyz_matrix(rotation), abs=1e-9)


def test_round_trip_at_gimbal_lock():
    rotation = (0.4, math.pi / 2, 0.0)
    back = euler_xyz_from_matrix(euler_xyz_matrix(rotation))
    assert euler_xyz_matrix(back) == pytest.approx(euler_xyz_matrix(rotation), abs=1e-9)


def test_axis_angle_follows_the_right_hand_rule():
    turned = axis_angle_matrix((0, 1, 0), math.pi / 2) @ np.array([0, 0, 1.0])
    assert turned == pytest.approx([1, 0, 0], abs=1e-12)


def test_turning_in_world_composes_with_the_existing_rotation():
    random.seed(9)
    for _ in range(50):
        start = (random.uniform(-2, 2), random.uniform(-1, 1), random.uniform(-2, 2))
        axis = np.array([random.gauss(0, 1) for _ in range(3)])
        angle = random.uniform(-2, 2)
        result = euler_xyz_matrix(turn_in_world(start, axis, angle))
        expected = axis_angle_matrix(axis, angle) @ euler_xyz_matrix(start)
        assert result == pytest.approx(expected, abs=1e-9)

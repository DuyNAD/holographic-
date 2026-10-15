from math import cos, sin

import pytest

from holostudio.avatar.depth import image_scale, relative_distance
from holostudio.tracking.types import Landmark

ASPECT = 16 / 9
# A flat open hand in metres (x right, y down like the image), wrist at the origin.
WORLD = tuple(Landmark(0.02 * (i % 5) - 0.04, -0.018 * (i // 5 + (i > 0)), 0.0) for i in range(21))


def project(world, centre, pixels_per_metre, angle=0.0):
    """Where a camera would draw the hand: in-plane turn, scale, no stretch."""
    out = []
    for p in world:
        x = p.x * cos(angle) - p.y * sin(angle)
        y = p.x * sin(angle) + p.y * cos(angle)
        out.append(
            Landmark(centre[0] + x * pixels_per_metre / ASPECT, centre[1] + y * pixels_per_metre, 0)
        )
    return tuple(out)


def test_twice_as_close_looks_twice_as_big():
    far = image_scale(project(WORLD, (0.5, 0.5), 2.0), WORLD, ASPECT)
    near = image_scale(project(WORLD, (0.3, 0.6), 4.0), WORLD, ASPECT)
    assert far == pytest.approx(2.0)
    assert near == pytest.approx(4.0)
    assert relative_distance(near, far) == pytest.approx(0.5)


def test_turning_the_hand_in_the_image_does_not_change_the_distance():
    still = image_scale(project(WORLD, (0.5, 0.5), 3.0), WORLD, ASPECT)
    turned = image_scale(project(WORLD, (0.5, 0.5), 3.0, angle=1.1), WORLD, ASPECT)
    assert turned == pytest.approx(still)


def test_missing_or_degenerate_hands_are_not_measured():
    assert image_scale((), (), ASPECT) is None
    dot = tuple(Landmark(0.5, 0.5, 0) for _ in range(21))
    assert image_scale(dot, WORLD, ASPECT) is None

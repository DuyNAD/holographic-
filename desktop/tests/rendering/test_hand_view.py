import time

import numpy as np
import pytest

from holostudio.avatar.pose import solve
from holostudio.avatar.profile import HandProfile, bone_lengths
from holostudio.gestures.engine import TrackedHand
from holostudio.rendering.hand_view import HandView
from holostudio.rendering.scene_view import SceneView

from ..avatar.hands import OPEN_HAND as BIG_WORLD
from ..avatar.test_depth import ASPECT, project

PROFILE = HandProfile(bone_lengths(BIG_WORLD), 2.0)


@pytest.fixture
def views(base):
    scene_view = SceneView(base, lambda _id: None, lambda _path: None)
    hands = HandView(base)
    yield scene_view, hands
    hands.destroy()
    scene_view.root.removeNode()


def screenshot(base):
    base.graphicsEngine.renderFrame()
    base.graphicsEngine.renderFrame()
    texture = base.win.getScreenshot()
    width, height = base.win.getXSize(), base.win.getYSize()
    pixels = np.frombuffer(bytes(texture.getRamImageAs("RGBA")), np.uint8)
    return pixels.reshape(height, width, 4)[::-1]


def is_skin(pixel):
    r, g, b, _a = (int(c) for c in pixel)
    return r > 120 and r > g > b and r - b > 40


def virtual(scene_view, centre, track_id=1):
    hand = TrackedHand(track_id, project(BIG_WORLD, centre, 2.0), BIG_WORLD, "point", ASPECT)
    return solve(hand, PROFILE, scene_view.view_rig())


def test_the_hand_is_drawn_in_skin_where_the_user_holds_it(views, base):
    scene_view, hands = views
    hands.update((virtual(scene_view, (0.35, 0.5)),))
    pixels = screenshot(base)
    height, width = pixels.shape[:2]
    # Camera x=0.35 is mirrored to the right side of the screen.
    right_side = pixels[:, width // 2 :]
    left_side = pixels[:, : width // 2]
    assert sum(is_skin(p) for p in right_side[::8, ::8].reshape(-1, 4)) > 50
    assert sum(is_skin(p) for p in left_side[::8, ::8].reshape(-1, 4)) == 0

    hands.update(())
    pixels = screenshot(base)
    assert sum(is_skin(p) for p in pixels[::8, ::8].reshape(-1, 4)) == 0


def test_two_hands_update_quickly(views):
    scene_view, hands = views
    pair = (virtual(scene_view, (0.35, 0.5), 1), virtual(scene_view, (0.65, 0.5), 2))
    hands.update(pair)
    start = time.perf_counter()
    for _ in range(50):
        hands.update(pair, touching=frozenset({2}))
    assert (time.perf_counter() - start) / 50 < 0.004

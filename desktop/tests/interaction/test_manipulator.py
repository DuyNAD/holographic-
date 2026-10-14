import math

import numpy as np
import pytest

from holostudio.gestures.engine import StableGesture
from holostudio.interaction.manipulator import (
    GestureManipulator,
    ViewQueries,
    intersect_depth_plane,
)
from holostudio.scene.history import (
    BeginInteraction,
    EndInteraction,
    Undo,
    create_history,
    reduce_history,
)
from holostudio.scene.rotation import euler_xyz_matrix
from holostudio.scene.state import Select, Translate
from holostudio.tracking.types import Landmark

CAMERA = np.array([6.5, 4.3, 7.5])
FOV = math.radians(42)
ASPECT = 16 / 9


def camera_basis():
    forward = -CAMERA / np.linalg.norm(CAMERA)
    right = np.cross(forward, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    return forward, right, up


def ray_through(point):
    forward, right, up = camera_basis()
    half_h = math.tan(FOV / 2)
    x = (point[0] * 2 - 1) * half_h * ASPECT
    y = (1 - point[1] * 2) * half_h
    direction = forward + right * x + up * y
    return CAMERA, direction / np.linalg.norm(direction)


def project(position):
    forward, right, up = camera_basis()
    relative = np.asarray(position) - CAMERA
    depth = relative @ forward
    half_h = math.tan(FOV / 2)
    x = (relative @ right) / depth / (half_h * ASPECT)
    y = (relative @ up) / depth / half_h
    return ((x + 1) / 2, (1 - y) / 2)


def gesture(name, screen=(0.5, 0.5), hand_index=0, palm=None):
    """A gesture with the index tip at `screen`; the palm points sit at `palm`."""
    px, py = palm if palm is not None else screen
    landmarks = [Landmark(1 - px, py, 0)] * 21
    landmarks[8] = Landmark(1 - screen[0], screen[1], 0)
    return StableGesture(hand_index, "Right", name, 1.0, tuple(landmarks), hand_index + 1)


def axes():
    _forward, right, up = camera_basis()
    return right, up


class Harness:
    def __init__(self, pick=lambda _p: "box-1", over_hud=lambda _p: False):
        self.history = create_history()
        self.actions = []
        self.now = 0.0

        def dispatch(action):
            self.actions.append(action)
            self.history = reduce_history(self.history, action)

        self.manipulator = GestureManipulator(
            ViewQueries(pick, ray_through, over_hud, axes), dispatch, clock=lambda: self.now
        )

    def frame(self, *gestures):
        self.now += 1 / 30
        self.manipulator.update(gestures, self.history.present)

    @property
    def box(self):
        return self.history.present.find("box-1")


def test_depth_plane_keeps_z():
    origin, direction = ray_through(project((0.8, 0.4, 1.6)))
    hit = intersect_depth_plane((origin, direction), 1.6)
    assert hit == pytest.approx([0.8, 0.4, 1.6], abs=1e-6)


def test_pinch_grabs_drags_and_releases_as_one_undo_entry():
    h = Harness()
    h.history = reduce_history(h.history, Select("box-1"))
    h.history = reduce_history(h.history, Translate(2, 1.5))  # move off the z=0 plane

    start = project(h.box.position)
    h.frame(gesture("pinch", start))
    assert isinstance(h.actions[1], BeginInteraction)

    target = (-1.0, 1.0, 1.5)
    h.frame(gesture("pinch", project(target)))
    assert h.box.position == pytest.approx(target, abs=1e-6)

    h.frame(gesture("open-palm"))
    assert isinstance(h.actions[-1], EndInteraction)
    assert len(h.history.past) == 2  # the translate + the whole drag


def test_pinch_over_the_hud_does_not_grab():
    h = Harness(over_hud=lambda _p: True)
    h.frame(gesture("pinch"))
    assert h.actions == []


def test_two_hand_pinch_scales_the_selected_object():
    h = Harness()
    h.history = reduce_history(h.history, Select("box-1"))

    h.frame(gesture("pinch", (0.4, 0.5)), gesture("pinch", (0.6, 0.5), hand_index=1))
    h.frame(gesture("pinch", (0.3, 0.5)), gesture("pinch", (0.7, 0.5), hand_index=1))

    assert h.box.scale == pytest.approx(2.0)


def test_losing_the_hand_ends_the_interaction():
    h = Harness()
    h.frame(gesture("pinch", project((-2.2, 0, 0))))
    assert h.manipulator.active
    h.frame()
    assert not h.manipulator.active
    assert isinstance(h.actions[-1], EndInteraction)


def test_the_other_hand_opening_does_not_cancel_a_drag():
    h = Harness()
    start = project((-2.2, 0, 0))
    h.frame(gesture("pinch", start))
    for step in range(1, 6):
        h.frame(
            gesture("open-palm", (0.8, 0.8), hand_index=1),
            gesture("pinch", (start[0] + 0.02 * step, start[1])),
        )
    assert h.manipulator.mode == "drag"
    assert h.box.position[0] > -2.2 + 0.3


def near_side_direction(history):
    """Where the object's camera-facing side points after its rotation."""
    forward, _right, _up = camera_basis()
    return euler_xyz_matrix(history.present.find("box-1").rotation) @ (
        np.linalg.inv(euler_xyz_matrix((0, 0.35, 0))) @ -forward
    )


def hold_and_swipe(h, swipes, order_flips=False):
    """Right hand holds the box with a fist; left hand swipes an open palm."""
    box_screen = project((-2.2, 0, 0))
    fist = gesture("fist", box_screen, hand_index=0)
    for point in swipes:
        palm = gesture("open-palm", point, hand_index=1)
        h.frame(*((palm, fist) if order_flips and len(h.actions) % 2 else (fist, palm)))
    return fist


def test_fist_holds_and_a_swipe_right_turns_the_near_side_right():
    h = Harness()
    # Two still frames (start holding, anchor the palm), then a quarter-window swipe.
    hold_and_swipe(h, [(0.5, 0.5), *[(0.5 + 0.025 * i, 0.5) for i in range(11)]])

    _forward, right, _up = camera_basis()
    assert h.manipulator.mode == "hold"
    assert near_side_direction(h.history) == pytest.approx(right, abs=1e-6)  # 90 degrees


def test_a_swipe_down_tips_the_near_side_down():
    h = Harness()
    hold_and_swipe(h, [(0.5, 0.4), *[(0.5, 0.4 + 0.025 * i) for i in range(11)]])

    _forward, _right, up = camera_basis()
    assert near_side_direction(h.history) == pytest.approx(-up, abs=1e-6)


def test_a_still_open_palm_does_not_drift_the_object():
    h = Harness()
    start = h.box.rotation
    hold_and_swipe(h, [(0.5 + 0.001 * (i % 3), 0.5) for i in range(30)])  # jitter only
    assert h.box.rotation == pytest.approx(start)


def test_swiping_without_a_holding_fist_does_nothing():
    h = Harness()
    h.history = reduce_history(h.history, Select("box-1"))
    for i in range(10):
        h.frame(gesture("open-palm", (0.5 + 0.03 * i, 0.5), hand_index=1))
    assert h.actions == []


def test_rotation_keeps_going_when_mediapipe_reorders_the_hands():
    ordered, flipped = Harness(), Harness()
    swipes = [(0.4 + 0.02 * i, 0.5) for i in range(15)]
    hold_and_swipe(ordered, swipes)
    hold_and_swipe(flipped, swipes, order_flips=True)
    assert flipped.box.rotation == pytest.approx(ordered.box.rotation, abs=1e-9)


def test_a_briefly_lost_fist_keeps_holding_but_a_long_loss_lets_go():
    h = Harness()
    box_screen = project((-2.2, 0, 0))
    fist = gesture("fist", box_screen)
    h.frame(fist)
    for _ in range(5):  # ~170 ms without the fist (motion blur)
        h.frame(gesture("open-palm", (0.6, 0.5), hand_index=1))
    assert h.manipulator.mode == "hold"
    for _ in range(10):  # ~330 ms more
        h.frame(gesture("open-palm", (0.6, 0.5), hand_index=1))
    assert h.manipulator.mode is None
    assert isinstance(h.actions[-1], EndInteraction)


def test_opening_the_holding_hand_ends_the_turn_as_one_undo_step():
    h = Harness()
    fist = hold_and_swipe(h, [(0.5 + 0.02 * i, 0.5) for i in range(10)])
    h.frame(gesture("open-palm", (0.5, 0.5), hand_index=fist.hand_index))
    assert h.manipulator.mode is None
    assert len(h.history.past) == 1
    turned = h.box.rotation
    h.history = reduce_history(h.history, Undo())
    assert h.box.rotation != turned


def test_a_fist_with_nothing_selected_holds_the_object_under_the_palm():
    h = Harness(pick=lambda _p: "sphere-1")
    h.frame(gesture("fist"))
    assert h.history.present.selected_id == "sphere-1"
    assert h.manipulator.mode == "hold"

    empty = Harness(pick=lambda _p: None)
    empty.frame(gesture("fist"))
    assert empty.manipulator.mode is None
    assert empty.actions == []

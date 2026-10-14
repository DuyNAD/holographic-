"""Tuning lock (v1, approved by the user).

These are the hand-tracking and interaction settings the user tested and approved.
This test fails on purpose if any of them changes, so a tweak can never slip in
unnoticed. To change one deliberately, update the value here in the same change
and say so in the commit message.
"""

import math

import pytest

from holostudio import config
from holostudio.app import controller
from holostudio.camera import capture
from holostudio.gestures import classifier, engine, filters, state_machine
from holostudio.interaction import dwell, manipulator
from holostudio.rendering import scene_view
from holostudio.scene import state
from holostudio.tracking import detector

LOCKED = {
    # Landmark smoothing (One Euro filter)
    (filters, "MIN_CUTOFF"): 1.2,
    (filters, "BETA"): 8.0,
    (filters, "DERIVATIVE_CUTOFF"): 1.0,
    # Gesture classification
    (classifier, "PINCH_RATIO"): 0.38,
    (classifier, "PINCH_RELEASE_RATIO"): 0.5,
    (classifier, "EXTENDED_RATIO"): 1.12,
    (classifier, "INDEX_FOLDED_RATIO"): 1.05,
    # Gesture debounce and hand following
    (state_machine, "ACTIVATION_FRAMES"): 2,
    (state_machine, "RELEASE_FRAMES"): 2,
    (state_machine, "MINIMUM_CONFIDENCE"): 0.6,
    (engine, "MATCH_DISTANCE"): 0.25,
    # Dwell-to-press
    (config, "DWELL_SECONDS"): 1.0,
    (dwell, "GRACE_SECONDS"): 0.25,
    # Fist + swipe rotation
    (manipulator, "TURN_PER_SCREEN"): 2 * math.pi,
    (manipulator, "SWIPE_DEAD_ZONE"): 0.004,
    (manipulator, "HOLD_GRACE_SECONDS"): 0.3,
    # Camera and tracking
    (config, "CAMERA_WIDTH"): 640,
    (config, "CAMERA_HEIGHT"): 360,
    (config, "CAMERA_FPS"): 30,
    (config, "MAX_TRACKED_HANDS"): 2,
    (detector, "DETECTION_CONFIDENCE"): 0.55,
    (capture, "MAX_FAILED_READS"): 30,
    (capture, "BLACK_LEVEL"): 3.0,
    (capture, "BLACK_SECONDS"): 2.0,
    # Scene and view
    (state, "MIN_SCALE"): 0.4,
    (state, "MAX_SCALE"): 2.5,
    (state, "SPAWN_SPACING"): 2.2,
    (state, "SPAWN_CLEARANCE"): 1.5,
    (scene_view, "CAMERA_POSITION"): (6.5, 4.3, 7.5),
    (scene_view, "VERTICAL_FOV"): 42.0,
    (scene_view, "SELECTED_TINT"): (1.15, 1.3, 1.4, 1),
    # HUD behaviour
    (config, "UNDO_TOAST_SECONDS"): 6.0,
    (controller, "SAVE_DELAY_SECONDS"): 0.25,
    (controller, "LIBRARY_PAGE_SIZE"): 4,
}


@pytest.mark.parametrize(
    ("module", "name", "expected"),
    [(module, name, value) for (module, name), value in LOCKED.items()],
    ids=[f"{module.__name__.rsplit('.', 1)[-1]}.{name}" for module, name in LOCKED],
)
def test_tuning_is_locked(module, name, expected):
    assert getattr(module, name) == expected, (
        f"{module.__name__}.{name} changed: this tuning is locked (see tests/test_tuning_lock.py)"
    )

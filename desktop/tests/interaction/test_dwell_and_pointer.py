import pytest

from holostudio.gestures.engine import StableGesture
from holostudio.interaction.coordinates import (
    landmark_distance,
    landmark_to_screen,
    screen_to_ndc,
)
from holostudio.interaction.dwell import DwellState, advance_dwell
from holostudio.interaction.pointer import HandPointer
from holostudio.tracking.types import Landmark


def hand_pointing_at(screen_x, screen_y, name="point"):
    landmarks = [Landmark(0, 0, 0)] * 21
    landmarks[8] = Landmark(1 - screen_x, screen_y, 0)
    return StableGesture(0, "Right", name, 1.0, tuple(landmarks))


def test_coordinates_mirror_the_camera():
    assert landmark_to_screen(Landmark(0.25, 0.75, 0)) == (0.75, 0.75)
    assert screen_to_ndc((0.75, 0.75)) == (0.5, -0.5)
    assert landmark_distance(Landmark(0, 0, 0), Landmark(0.3, 0.4, 9)) == 0.5


def test_dwell_fires_once_after_one_second():
    step = advance_dwell(DwellState(), "add", 0.0)
    assert (step.progress, step.fire) == (0.0, False)
    step = advance_dwell(step.state, "add", 0.5)
    assert (step.progress, step.fire) == (0.5, False)
    step = advance_dwell(step.state, "add", 1.0)
    assert (step.progress, step.fire) == (1.0, True)
    assert advance_dwell(step.state, "add", 3.0).fire is False


def test_dwell_moves_to_a_new_target_after_the_grace_period():
    state = advance_dwell(DwellState(), "add", 0.0).state
    state = advance_dwell(state, "add", 0.9).state
    held = advance_dwell(state, "delete", 0.95)  # within the grace period: keep "add"
    assert held.state.target == "add"
    step = advance_dwell(held.state, "delete", 1.3)  # grace over: start on "delete"
    assert (step.state.target, step.progress) == ("delete", 0.0)
    assert advance_dwell(step.state, "delete", 2.31).fire


def test_a_brief_slip_off_the_button_keeps_the_progress():
    state = advance_dwell(DwellState(), "add", 0.0).state
    state = advance_dwell(state, "add", 0.5).state
    slip = advance_dwell(state, None, 0.6)
    assert slip.state.target == "add" and slip.progress == pytest.approx(0.6)
    state = advance_dwell(slip.state, "add", 0.7).state
    assert advance_dwell(state, "add", 1.0).fire


def test_dwell_rearms_after_really_leaving():
    state = advance_dwell(advance_dwell(DwellState(), "add", 0).state, "add", 1).state
    state = advance_dwell(state, None, 1.5).state
    assert state.target is None
    state = advance_dwell(state, "add", 1.6).state
    assert advance_dwell(state, "add", 2.6).fire


def test_pointer_presses_the_button_under_the_pointing_finger():
    buttons = {"add": (0.0, 0.0, 0.2, 0.2)}

    def target_at(point):
        for name, (x0, y0, x1, y1) in buttons.items():
            if x0 <= point[0] <= x1 and y0 <= point[1] <= y1:
                return name
        return None

    pointer = HandPointer(target_at)
    frame = pointer.update((hand_pointing_at(0.1, 0.1),), 0.0)
    assert frame.hover == "add"
    assert frame.marks[0].is_pointer

    assert pointer.update((hand_pointing_at(0.1, 0.1),), 0.6).progress == 0.6
    assert pointer.update((hand_pointing_at(0.1, 0.1),), 1.0).pressed == "add"
    assert pointer.update((hand_pointing_at(0.1, 0.1),), 1.4).pressed is None


def test_only_the_point_gesture_presses_buttons():
    pointer = HandPointer(lambda _p: "add")
    for now in (0.0, 1.0, 2.0):
        frame = pointer.update((hand_pointing_at(0.1, 0.1, name="pinch"),), now)
    # (only the pointing finger can hover or press)
    assert frame.pressed is None
    assert frame.hover is None
    assert frame.marks[0].gesture == "pinch"
    assert not frame.marks[0].is_pointer

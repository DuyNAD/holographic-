from holostudio.calibration.flow import (
    Calibration,
    CalibrationInputs,
    load_calibrated,
    save_calibrated,
)


def inputs(camera=False, requesting=False, hand=False, pinch=False):
    return CalibrationInputs(camera, requesting, hand, pinch)


def test_requires_camera_hand_and_pinch_before_completion():
    flow = Calibration(open_=True)

    assert flow.press("start", inputs()) is None
    assert flow.step == 1
    assert flow.press("camera", inputs()) == "start-camera"
    assert flow.press("next", inputs()) is None  # no 'next' button until the camera is on
    assert flow.step == 1

    assert flow.press("next", inputs(camera=True)) is None
    assert flow.step == 2
    flow.press("next", inputs(camera=True))  # disabled without a hand
    assert flow.step == 2

    flow.press("next", inputs(camera=True, hand=True))
    assert flow.step == 3
    flow.press("next", inputs(camera=True, hand=True))  # disabled without a pinch
    assert flow.step == 3

    flow.press("next", inputs(camera=True, hand=True, pinch=True))
    assert flow.step == 4
    assert flow.press("finish", inputs()) == "complete"
    assert not flow.open


def test_can_be_skipped_from_any_step_without_a_camera():
    for step in range(4):
        flow = Calibration(open_=True)
        flow.step = step
        assert flow.press("skip", inputs()) == "skip"
        assert not flow.open


def test_camera_button_is_disabled_while_connecting():
    view = Calibration(True)
    view.step = 1
    button = view.view(inputs(requesting=True)).buttons[0]
    assert (button.label, button.enabled) == ("Đang kết nối…", False)


def test_restart_and_persistence(tmp_path):
    flow = Calibration(open_=False)
    flow.restart()
    assert flow.open and flow.step == 0

    settings = tmp_path / "settings.json"
    assert load_calibrated(settings) is False
    save_calibrated(settings)
    assert load_calibrated(settings) is True

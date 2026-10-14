import pytest

from holostudio.app.controller import StudioController
from holostudio.assets.library import ModelLibrary
from holostudio.calibration.flow import load_calibrated
from holostudio.scene.state import create_initial_scene
from holostudio.scene.storage import load_scene
from holostudio.tracking.types import TrackingState


class FakeCamera:
    def __init__(self):
        self.status = "idle"
        self.message = "Camera đang tắt."
        self.starts = 0

    @property
    def active(self):
        return self.status == "active"

    def start(self):
        self.starts += 1
        self.status = "active"

    def stop(self):
        self.status = "idle"


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@pytest.fixture
def make(tmp_path, glb_file):
    def factory(calibrated=True, pick=None):
        clock = Clock()
        library = ModelLibrary(tmp_path / "library", parse=lambda _p: None)
        controller = StudioController(
            library=library,
            camera=FakeCamera(),
            scene_file=tmp_path / "scene.json",
            settings_file=tmp_path / "settings.json",
            calibrated=calibrated,
            pick_file=pick or (lambda: glb_file),
            clock=clock,
        )
        return controller, clock

    return factory


def hud(controller):
    return controller.hud_context(1280, 720, TrackingState(), ())


def test_menu_panels_toggle_and_collapse(make):
    controller, _ = make()
    controller.press("menu.add")
    assert controller.panel == "add"
    controller.press("menu.guide")
    assert controller.panel == "guide"
    controller.press("menu.guide")
    assert controller.panel is None

    controller.press("menu.add")
    controller.press("menu.toggle")
    assert controller.collapsed and controller.panel is None


def test_add_delete_and_undo_from_the_toast(make):
    controller, clock = make()
    controller.press("shape.cylinder")
    added = controller.scene.selected
    assert added.kind == "cylinder"
    assert added.position == (0, 1.9, 0)  # free slot, not on top of others

    controller.press("menu.delete")
    assert controller.scene.find(added.id) is None
    assert hud(controller).toast == "Đã xóa “Khối trụ”"

    controller.press("toast.undo")
    assert controller.scene.find(added.id) is not None
    assert controller.toast is None


def test_toast_expires(make):
    controller, clock = make()
    controller.click_scene("box-1")
    controller.key("delete")
    assert controller.toast
    clock.now += 6.1
    controller.tick()
    assert controller.toast is None


def test_upload_stores_once_and_places_many_times(make):
    controller, _ = make()
    controller.press("library.upload")
    assert len(controller.library.items) == 1
    asset_id = controller.library.items[0].id

    controller.press(f"library.place:{asset_id}")
    controller.press(f"library.place:{asset_id}")
    models = [obj for obj in controller.scene.objects if obj.asset_id == asset_id]
    assert len(models) == 3
    assert len({obj.position for obj in models}) == 3

    controller.press(f"library.remove:{asset_id}")
    assert controller.library_error
    assert len(controller.library.items) == 1


def test_cancelled_upload_changes_nothing(make):
    controller, _ = make(pick=lambda: None)
    controller.press("library.upload")
    assert controller.library.items == []
    assert controller.scene == create_initial_scene()


def test_keyboard_shortcuts(make):
    controller, _ = make()
    controller.key("arrow_right")  # nothing selected
    assert controller.scene == create_initial_scene()

    controller.click_scene("box-1")
    controller.key("arrow_right")
    controller.key("=")
    assert controller.scene.selected.position[0] == pytest.approx(-2.0)
    assert controller.scene.selected.scale == pytest.approx(1.1)
    controller.key("control-z")
    controller.key("control-z")
    assert controller.scene.selected.position[0] == -2.2
    controller.key("control-y")
    assert controller.scene.selected.position[0] == pytest.approx(-2.0)


def test_calibration_blocks_the_menu_and_can_be_skipped(make):
    controller, _ = make(calibrated=False)
    assert hud(controller).calibration is not None

    controller.press("menu.add")
    controller.key("delete")
    assert controller.panel is None

    controller.key("escape")
    assert not controller.calibration.open
    assert hud(controller).calibration is None


def test_calibration_starts_the_camera_and_remembers_completion(make, tmp_path):
    controller, _ = make(calibrated=False)
    controller.press("calibration.start")
    controller.press("calibration.camera")
    assert controller.camera.active
    controller.update_inputs(TrackingState(), ())
    controller.press("calibration.next")
    assert controller.calibration.step == 2

    controller.calibration.step = 4
    controller.press("calibration.finish")
    assert load_calibrated(tmp_path / "settings.json")


def test_saves_shortly_after_a_change(make, tmp_path):
    controller, clock = make()
    controller.click_scene("box-1")
    controller.key("delete")
    controller.tick()
    assert not (tmp_path / "scene.json").exists()

    clock.now += 0.3
    controller.tick()
    assert len(load_scene(tmp_path / "scene.json").objects) == 2


def test_camera_toggle(make):
    controller, _ = make()
    controller.press("camera.toggle")
    assert controller.camera.active
    assert hud(controller).camera_active
    controller.press("camera.toggle")
    assert not controller.camera.active


def test_a_camera_sending_black_frames_can_still_be_turned_off(make):
    controller, _ = make()
    controller.camera.status = "blocked"
    controller.camera.message = "Camera chỉ trả về hình đen."
    context = hud(controller)
    assert context.camera_running and not context.camera_active
    controller.press("camera.toggle")
    assert controller.camera.status == "idle"


def test_hud_explains_a_fist_with_nothing_selected(make):
    from holostudio.gestures.engine import StableGesture
    from holostudio.tracking.types import Landmark

    controller, _ = make()
    fist = StableGesture(0, "Right", "fist", 1.0, (Landmark(0.5, 0.5, 0),) * 21, 1)
    tracking = TrackingState("tracking")
    assert controller.hud_context(1280, 720, tracking, (fist,)).gesture_label == (
        "Nắm · chưa chọn vật"
    )
    controller.click_scene("box-1")
    assert controller.hud_context(1280, 720, tracking, (fist,)).gesture_label == "Nắm tay"

"""The single place where every input becomes an action.

Mouse clicks, hand dwell presses, and keyboard shortcuts all call `press` or
`key`, so the three input methods always behave the same way. Nothing here
depends on Panda3D, which keeps the whole app logic testable.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from holostudio.assets.library import ModelLibrary
from holostudio.calibration.flow import (
    Calibration,
    CalibrationInputs,
    save_calibrated,
)
from holostudio.camera.capture import STATUS_LABELS, CameraStream
from holostudio.config import UNDO_TOAST_SECONDS
from holostudio.gestures.engine import GESTURE_LABELS, StableGesture
from holostudio.hud.widgets import HudContext, LibraryEntry
from holostudio.scene.history import HistoryAction, Redo, Undo, create_history, reduce_history
from holostudio.scene.state import (
    AddObject,
    RemoveObject,
    Rotate,
    Scale,
    Select,
    Translate,
    create_model_object,
    create_shape_object,
    find_spawn_position,
)
from holostudio.scene.storage import load_scene, save_scene
from holostudio.tracking.types import TrackingState

SAVE_DELAY_SECONDS = 0.25
LIBRARY_PAGE_SIZE = 4

GUIDE_ROWS = (
    ("Trỏ", "Giơ ngón trỏ", "Di chuyển con trỏ"),
    ("Giữ để bấm", "Trỏ vào nút, giữ yên 1 giây", "Bấm nút"),
    ("Chụm", "Chụm ngón cái và ngón trỏ", "Chọn và kéo"),
    ("Nắm + phẩy", "Một tay nắm giữ vật, tay kia mở và phẩy", "Xoay 3D"),
    ("Mở tay", "Mở bàn tay đang nắm hoặc chụm", "Thả vật thể"),
    ("Hai tay chụm", "Chụm ngón trên hai tay", "Đổi kích thước"),
)

KEY_ACTIONS: dict[str, HistoryAction] = {
    "arrow_left": Translate(0, -0.2),
    "arrow_right": Translate(0, 0.2),
    "arrow_up": Translate(1, 0.2),
    "arrow_down": Translate(1, -0.2),
    "q": Rotate(1, -0.15),
    "e": Rotate(1, 0.15),
    "-": Scale(-0.1),
    "=": Scale(0.1),
}


def format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    return f"{max(1, round(size / 1024))} KB"


class StudioController:
    def __init__(
        self,
        library: ModelLibrary,
        camera: CameraStream,
        scene_file: Path,
        settings_file: Path,
        calibrated: bool,
        pick_file: Callable[[], Path | None],
        on_camera_start: Callable[[], None] = lambda: None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.library = library
        self.camera = camera
        self._scene_file = scene_file
        self._settings_file = settings_file
        self._pick_file = pick_file
        self._on_camera_start = on_camera_start
        self._clock = clock

        self.history = create_history(load_scene(scene_file))
        self.calibration = Calibration(open_=not calibrated)
        self.collapsed = False
        self.panel: str | None = None
        self.library_page = 0
        self.library_message = "GLB tối đa 25 MB · lưu trên thiết bị."
        self.library_error = False
        self.toast: str | None = None
        self._toast_until = 0.0
        self._saved_objects = self.history.present.objects
        self._dirty_since: float | None = None
        self._calibration_inputs = CalibrationInputs(False, False, False, False)

    # --- scene ---------------------------------------------------------------

    @property
    def scene(self):
        return self.history.present

    def dispatch(self, action: HistoryAction) -> None:
        self.history = reduce_history(self.history, action)
        if self.history.present.objects != self._saved_objects and self._dirty_since is None:
            self._dirty_since = self._clock()

    def delete_selected(self) -> None:
        selected = self.scene.selected
        if selected is None:
            return
        self.dispatch(RemoveObject(selected.id))
        self.toast = f"Đã xóa “{selected.name}”"
        self._toast_until = self._clock() + UNDO_TOAST_SECONDS

    def _spawn(self):
        return find_spawn_position(self.scene.objects)

    # --- inputs --------------------------------------------------------------

    def update_inputs(self, tracking: TrackingState, gestures: tuple[StableGesture, ...]) -> None:
        self._calibration_inputs = CalibrationInputs(
            camera_active=self.camera.active,
            camera_requesting=self.camera.status == "requesting",
            hand_tracked=tracking.status == "tracking",
            pinch_seen=any(g.name == "pinch" for g in gestures),
        )

    def press(self, widget_id: str) -> None:
        """Handles a HUD button, whether it was clicked or pressed by hand."""
        if widget_id.startswith("calibration."):
            self._press_calibration(widget_id.removeprefix("calibration."))
            return
        if self.calibration.open:
            return

        if widget_id == "menu.toggle":
            self.collapsed = not self.collapsed
            self.panel = None
        elif widget_id in ("menu.add", "menu.guide"):
            name = widget_id.removeprefix("menu.")
            self.panel = None if self.panel == name else name
        elif widget_id == "menu.delete":
            self.delete_selected()
        elif widget_id == "panel.close":
            self.panel = None
        elif widget_id.startswith("shape."):
            obj = create_shape_object(widget_id.removeprefix("shape."), self._spawn())
            self.dispatch(AddObject(obj))
            self._report(f"Đã thêm “{obj.name}” vào cảnh.")
        elif widget_id.startswith("library.place:"):
            item = self.library.get(widget_id.removeprefix("library.place:"))
            if item:
                self.dispatch(AddObject(create_model_object(item.id, item.name, self._spawn())))
                self._report(f"Đã lấy “{item.name}” từ kho.")
        elif widget_id.startswith("library.remove:"):
            result = self.library.remove(widget_id.removeprefix("library.remove:"), self.history)
            self._report(result.message, error=not result.ok)
            self._clamp_page()
        elif widget_id == "library.prev":
            self.library_page = max(0, self.library_page - 1)
        elif widget_id == "library.next":
            self.library_page += 1
            self._clamp_page()
        elif widget_id == "library.upload":
            self._upload()
        elif widget_id == "guide.recalibrate":
            self.panel = None
            self.calibration.restart()
        elif widget_id == "toast.undo":
            self.dispatch(Undo())
            self.toast = None
        elif widget_id == "camera.toggle":
            self.toggle_camera()

    def key(self, name: str) -> None:
        if name == "escape":
            if self.calibration.open:
                self._press_calibration("skip")
            else:
                self.panel = None
            return
        if self.calibration.open:
            return
        if name == "control-z":
            self.dispatch(Undo())
        elif name in ("control-y", "control-shift-z"):
            self.dispatch(Redo())
        elif name == "delete":
            self.delete_selected()
        elif name in KEY_ACTIONS and self.scene.selected:
            self.dispatch(KEY_ACTIONS[name])

    def click_scene(self, object_id: str | None) -> None:
        if not self.calibration.open:
            self.dispatch(Select(object_id))

    @property
    def camera_running(self) -> bool:
        """The camera is open, even if it only delivers black frames."""
        return self.camera.status in ("active", "blocked")

    def toggle_camera(self) -> None:
        if self.camera_running:
            self.camera.stop()
        else:
            self.camera.start()
            self._on_camera_start()

    def _press_calibration(self, action: str) -> None:
        effect = self.calibration.press(action, self._calibration_inputs)
        if effect == "start-camera" and not self.camera.active:
            self.camera.start()
            self._on_camera_start()
        elif effect == "complete":
            save_calibrated(self._settings_file)

    def _upload(self) -> None:
        path = self._pick_file()
        if path is None:
            return
        result = self.library.import_file(path)
        self._report(result.message, error=not result.ok)
        if result.item:
            self.library_page = 0
            self.dispatch(
                AddObject(create_model_object(result.item.id, result.item.name, self._spawn()))
            )

    def _report(self, message: str, error: bool = False) -> None:
        self.library_message = message
        self.library_error = error

    def _clamp_page(self) -> None:
        pages = max(1, -(-len(self.library.items) // LIBRARY_PAGE_SIZE))
        self.library_page = min(self.library_page, pages - 1)

    # --- per frame -----------------------------------------------------------

    def tick(self) -> None:
        now = self._clock()
        if self.toast and now >= self._toast_until:
            self.toast = None
        if self._dirty_since is not None and now - self._dirty_since >= SAVE_DELAY_SECONDS:
            self.save()

    def save(self) -> None:
        save_scene(self.scene, self._scene_file)
        self._saved_objects = self.scene.objects
        self._dirty_since = None

    def hud_context(
        self,
        width: int,
        height: int,
        tracking: TrackingState,
        gestures: tuple[StableGesture, ...],
    ) -> HudContext:
        primary = gestures[0] if gestures else None
        if any(g.name == "fist" for g in gestures) and self.scene.selected is None:
            # The fist found no object under it: say why nothing turns.
            gesture_label = "Nắm · chưa chọn vật"
        elif primary:
            gesture_label = GESTURE_LABELS[primary.name]
        elif tracking.status == "tracking":
            gesture_label = "Đang phân tích"
        else:
            gesture_label = "Chưa nhận diện"
        # Rounded so the HUD is only redrawn when something visible changes.
        confidence = round(primary.confidence, 1) if primary else 0.0

        camera_active = self.camera.active
        selected = self.scene.selected
        return HudContext(
            width=width,
            height=height,
            collapsed=self.collapsed,
            panel=self.panel,
            selected_name=selected.name if selected else None,
            gesture_label=gesture_label,
            confidence=confidence,
            camera_badge=STATUS_LABELS[self.camera.status],
            camera_message=self.camera.message,
            camera_active=camera_active,
            camera_running=self.camera_running,
            camera_busy=self.camera.status == "requesting",
            tracking_message=tracking.message
            if camera_active
            else "Video chỉ xử lý trên thiết bị.",
            library=tuple(
                LibraryEntry(item.id, item.name, format_size(item.size))
                for item in self.library.items
            ),
            library_page=self.library_page,
            library_message=self.library_message,
            library_error=self.library_error,
            toast=self.toast,
            calibration=(
                self.calibration.view(self._calibration_inputs) if self.calibration.open else None
            ),
            guide_rows=GUIDE_ROWS,
        )

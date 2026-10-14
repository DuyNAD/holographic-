"""The Panda3D window: runs every stage once per frame.

Per frame: tracking result -> gestures -> hand pointer (HUD presses) and
manipulator (3D edits) -> controller -> 3D view and HUD.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties

from holostudio import config
from holostudio.assets.library import ModelLibrary
from holostudio.assets.loader import load_glb
from holostudio.calibration.flow import load_calibrated
from holostudio.camera.capture import CameraStream
from holostudio.gestures.engine import GestureEngine
from holostudio.hud.camera_preview import prepare_preview
from holostudio.hud.view import HudView
from holostudio.hud.widgets import Widget, build_hud, over_hud, press_target
from holostudio.interaction.manipulator import GestureManipulator, ViewQueries
from holostudio.interaction.pointer import HandPointer
from holostudio.rendering.scene_view import SceneView
from holostudio.tracking.worker import TrackingWorker

from .controller import StudioController

KEY_EVENTS = (
    "arrow_left",
    "arrow_right",
    "arrow_up",
    "arrow_down",
    "q",
    "e",
    "-",
    "=",
    "delete",
    "escape",
    "control-z",
    "control-y",
    "control-shift-z",
    "enter",
)


def pick_glb_file() -> Path | None:
    """Native file dialog; it needs a mouse or keyboard to choose the file."""
    import tkinter
    from tkinter import filedialog

    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        chosen = filedialog.askopenfilename(
            title="Chọn file GLB", filetypes=[("GLB 2.0", "*.glb"), ("Tất cả", "*.*")]
        )
    finally:
        root.destroy()
    return Path(chosen) if chosen else None


class StudioApp(ShowBase):
    def __init__(
        self,
        camera: CameraStream | None = None,
        tracking: TrackingWorker | None = None,
        data_dir: Path = config.DATA_DIR,
        pick_file: Callable[[], Path | None] = pick_glb_file,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__()
        self._clock = clock
        self._configure_window()

        self.camera_stream = camera or CameraStream()
        self.tracking = tracking or TrackingWorker(self.camera_stream)
        self.library = ModelLibrary(data_dir / "library")
        self.controller = StudioController(
            library=self.library,
            camera=self.camera_stream,
            scene_file=data_dir / "scene.json",
            settings_file=data_dir / "settings.json",
            calibrated=load_calibrated(data_dir / "settings.json"),
            pick_file=pick_file,
            on_camera_start=self.tracking.start,
            on_designer_request=self.tracking.request_designer,
            on_designer_confirm=self.tracking.confirm_designer,
            on_designer_cancel=self.tracking.cancel_designer,
            clock=clock,
        )

        self.scene_view = SceneView(self, self._model_path, load_glb)
        self.hud = HudView(self)
        self.gestures = GestureEngine()
        self.widgets: tuple[Widget, ...] = ()
        self.pointer = HandPointer(self._pointer_target)
        self.manipulator = GestureManipulator(
            ViewQueries(
                self.scene_view.pick,
                self.scene_view.ray,
                self._over_hud,
                self.scene_view.camera_axes,
            ),
            self.controller.dispatch,
            clock=clock,
        )
        self._last_preview_index = -1
        self._designer_locked = False
        self._designer_status = "unset"

        self.accept("mouse1", self._on_click)
        self.accept("window-event", self._on_window_event)
        for event in KEY_EVENTS:
            self.accept(event, self.controller.key, [event])
            self.accept(f"{event}-repeat", self.controller.key, [event])
        self.exitFunc = self.close_studio
        self.taskMgr.add(self._frame, "studio-frame")

    def _configure_window(self) -> None:
        if self.win is None or not hasattr(self.win, "requestProperties"):
            return
        properties = WindowProperties()
        properties.setTitle("Holographic Studio")
        self.win.requestProperties(properties)

    def _model_path(self, asset_id: str) -> Path | None:
        return self.library.path_of(asset_id) if self.library.get(asset_id) else None

    # --- size helpers --------------------------------------------------------

    def _size(self) -> tuple[int, int]:
        return self.win.getXSize(), self.win.getYSize()

    def _to_pixels(self, point) -> tuple[float, float]:
        width, height = self._size()
        return (point[0] * width, point[1] * height)

    def _pointer_target(self, point) -> str | None:
        """The button the hand pointer may press here (hands are limited until a
        designer is locked; the mouse is never limited)."""
        target = press_target(self.widgets, self._to_pixels(point))
        if target and self.controller.hand_may_press(target, self._designer_status):
            return target
        return None

    def _over_hud(self, point) -> bool:
        return over_hud(self.widgets, self._to_pixels(point))

    # --- events --------------------------------------------------------------

    def _on_click(self) -> None:
        if not self.mouseWatcherNode.hasMouse():
            return
        mouse = self.mouseWatcherNode.getMouse()
        point = ((mouse.x + 1) / 2, (1 - mouse.y) / 2)
        target = press_target(self.widgets, self._to_pixels(point))
        if target:
            self.controller.press(target)
        elif not self._over_hud(point):
            self.controller.click_scene(self.scene_view.pick(point))

    def _on_window_event(self, window) -> None:
        # ShowBase's own handler must still run: it rescales the 2D layers (the HUD)
        # on resize and exits the app when the window is closed.
        ShowBase.windowEvent(self, window)
        if window is self.win and window.isValid():
            self.scene_view.update_aspect()

    # --- frame ---------------------------------------------------------------

    def step(self) -> None:
        """One frame of the whole pipeline (also used by tests and tools)."""
        controller = self.controller
        tracking = self.tracking.state
        self._designer_locked = tracking.designer.locked
        self._designer_status = tracking.designer.status
        # Only the designer's hands control the app once a designer is locked, and only
        # the recorded person's hands can confirm them. Before that, hands may still
        # drive calibration and press the designer button.
        mine_only = self._designer_locked or tracking.designer.pending
        controlling = tracking.designer_only() if mine_only else tracking
        gestures = self.gestures.update(controlling)
        controller.update_inputs(tracking, gestures)

        width, height = self._size()
        self.widgets = build_hud(controller.hud_context(width, height, tracking, gestures))

        pointer_frame = self.pointer.update(gestures, self._clock())
        if pointer_frame.pressed:
            controller.press(pointer_frame.pressed)

        if controller.calibration.open or not self._designer_locked:
            self.manipulator.reset()
        else:
            self.manipulator.update(gestures, controller.scene)

        controller.tick()
        # Rebuild after presses so the HUD shows their effect in the same frame.
        self.widgets = build_hud(controller.hud_context(width, height, tracking, gestures))
        self.scene_view.sync(controller.scene)
        self.hud.render_widgets(self.widgets, width, height)
        self.hud.render_pointer(pointer_frame, width, height)
        self._update_preview(tracking)

    def _update_preview(self, tracking) -> None:
        frame = self.camera_stream.latest_frame()
        if frame is None:
            self.hud.update_camera(None)
            self._last_preview_index = -1
            return
        if frame.index == self._last_preview_index:
            return
        self._last_preview_index = frame.index
        hands = tracking.frame.hands if tracking.status == "tracking" else ()
        designer = tracking.designer
        self.hud.update_camera(
            prepare_preview(
                frame.image,
                hands,
                self.hud.camera_aspect,
                designer_face=designer.face,
                other_faces=designer.other_faces,
                candidate=designer.pending,
            )
        )

    def _frame(self, task):
        self.step()
        return task.cont

    def close_studio(self) -> None:
        """Saves the scene and releases the camera; runs when the window closes."""
        self.controller.save()
        self.tracking.stop()
        self.camera_stream.stop()
